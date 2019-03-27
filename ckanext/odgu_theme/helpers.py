import copy
import re

from ckan import logic, model
from ckan.common import config, c, is_flask_request
from ckan.lib import base
from ckan.lib.activity_streams import activity_stream_actions_with_detail, activity_stream_string_functions, \
    activity_stream_string_icons, activity_snippet_functions
from ckan.lib.helpers import check_access, map_pylons_to_flask_route_name, _link_active, _link_to
from ckan.logic.action.get import recently_changed_packages_activity_list
from webhelpers.html import literal


def build_main(*args):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <li><a href="...">title</a></li>
    '''
    output = ''
    for item in args:
        menu_item, title = item[:2]
        if len(item) == 3 and not check_access(item[2]):
            continue
        output += _make_menu_item(menu_item, title)
    return output


def _make_menu_item(menu_item, title, **kw):
    ''' build a navigation item used for example breadcrumbs

    outputs <div class="main-menu__item"><a href="..."></i> title</a></li>

    :param menu_item: the name of the defined menu item defined in
    config/routing as the named route of the same name
    :type menu_item: string
    :param title: text used for the link
    :type title: string
    :param **kw: additional keywords needed for creating url eg id=...

    :rtype: HTML literal

    This function is called by wrapper functions.
    '''
    menu_item = map_pylons_to_flask_route_name(menu_item)
    _menu_items = config['routes.named_routes']
    if menu_item not in _menu_items:
        raise Exception('menu item `%s` cannot be found' % menu_item)
    item = copy.copy(_menu_items[menu_item])
    item.update(kw)
    active = _link_active(item)
    needed = item.pop('needed')
    for need in needed:
        if need not in kw:
            raise Exception('menu item `%s` need parameter `%s`'
                            % (menu_item, need))
    link = _link_to(title, menu_item, suppress_active_class=True, **item)
    if active:
        return literal('<div class="main-menu__item">') + link + literal('</div>')
    return literal('<div class="main-menu__item">') + link + literal('</div>')


def get_all_groups():
    '''Returns a list of favourite group the form
    of organization_list action function
    '''
    groups = all_group_org(get_action='group_show',
                           list_action='group_list',)
    return groups


def all_group_org(get_action, list_action):
    def get_group(id):
        context = {'ignore_auth': True,
                   'limits': {'packages': 2},
                   'for_view': True}
        data_dict = {'id': id,
                     'include_datasets': True}

        try:
            out = logic.get_action(get_action)(context, data_dict)
        except logic.NotFound:
            return None
        return out

    groups_data = []

    extras = logic.get_action(list_action)({}, {})

    # list of found ids to prevent duplicates
    found = []
    for group_name in extras:
        group = get_group(group_name)
        if not group:
            continue
        # check if duplicate
        if group['id'] in found:
            continue
        found.append(group['id'])
        groups_data.append(group)

    return groups_data


def recently_changed_packages_activity_stream_main(limit=None):
    if limit:
        data_dict = {'limit': limit}
    else:
        data_dict = {}
    context = {'model': model, 'session': model.Session, 'user': c.user}
    activity_stream = recently_changed_packages_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'package',
        'action': 'activity',
        'offset': offset,
    }
    return activity_list_to_html_main(
        context, activity_stream, extra_vars)


def activity_list_to_html_main(context, activity_stream, extra_vars):
    """Return the given activity stream as a snippet of HTML.

    :param activity_stream: the activity stream to render
    :type activity_stream: list of activity dictionaries
    :param extra_vars: extra variables to pass to the activity stream items
        template when rendering it
    :type extra_vars: dictionary

    :rtype: HTML-formatted string

    """

    activity_list = []
    for activity in activity_stream:
        detail = None
        activity_type = activity['activity_type']
        # Some activity types may have details.
        if activity_type in activity_stream_actions_with_detail:
            details = logic.get_action('activity_detail_list')(context=context,
                data_dict={'id': activity['id']})
            # If an activity has just one activity detail then render the
            # detail instead of the activity.
            if len(details) == 1:
                detail = details[0]
                object_type = detail['object_type']

                if object_type == 'PackageExtra':
                    object_type = 'package_extra'

                new_activity_type = '%s %s' % (detail['activity_type'],
                                            object_type.lower())
                if new_activity_type in activity_stream_string_functions:
                    activity_type = new_activity_type

        if not activity_type in activity_stream_string_functions:
            raise NotImplementedError("No activity renderer for activity "
                "type '%s'" % activity_type)

        if activity_type in activity_stream_string_icons:
            activity_icon = activity_stream_string_icons[activity_type]
        else:
            activity_icon = activity_stream_string_icons['undefined']

        activity_msg = activity_stream_string_functions[activity_type](context,
                activity)

        # Get the data needed to render the message.
        matches = re.findall('\{([^}]*)\}', activity_msg)
        data = {}
        for match in matches:
            snippet = activity_snippet_functions[match](activity, detail)
            data[str(match)] = snippet

        activity_list.append({'msg': activity_msg,
                              'type': activity_type.replace(' ', '-').lower(),
                              'icon': activity_icon,
                              'data': data,
                              'timestamp': activity['timestamp'],
                              'is_new': activity.get('is_new', False)})
    extra_vars['activities'] = activity_list

    # TODO: Do this properly without having to check if it's Flask or not
    if is_flask_request():
        return base.render('home/activity_stream_items.html',
                           extra_vars=extra_vars)
    else:
        return literal(base.render('home/activity_stream_items.html',
                       extra_vars=extra_vars))
