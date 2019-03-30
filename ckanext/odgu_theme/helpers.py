import copy
import datetime
import re

import ckan.plugins.toolkit as toolkit
from ckan import logic, model
from ckan.lib.helpers import check_access, map_pylons_to_flask_route_name, _link_active, _link_to, \
    _datestamp_to_datetime
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
    _menu_items = toolkit.config['routes.named_routes']
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
    context = {'model': model, 'session': model.Session, 'user': toolkit.c.user}
    activity_stream = recently_changed_packages_activity_list(context, data_dict)
    return activity_stream


def render_datetime_ukr(datetime_, date_format=None, with_hours=False):
    '''Render a datetime object or timestamp string as a localised date or
    in the requested format.
    If timestamp is badly formatted, then a blank string is returned.

    :param datetime_: the date
    :type datetime_: datetime or ISO string format
    :param date_format: a date format
    :type date_format: string
    :param with_hours: should the `hours:mins` be shown
    :type with_hours: bool

    :rtype: string
    '''
    datetime_ = _datestamp_to_datetime(datetime_)
    if not datetime_:
        return ''

    # if date_format was supplied we use it
    if date_format:

        # See http://bugs.python.org/issue1777412
        if datetime_.year < 1900:
            year = str(datetime_.year)

            date_format = re.sub('(?<!%)((%%)*)%y',
                                 r'\g<1>{year}'.format(year=year[-2:]),
                                 date_format)
            date_format = re.sub('(?<!%)((%%)*)%Y',
                                 r'\g<1>{year}'.format(year=year),
                                 date_format)

            datetime_ = datetime.datetime(2016, datetime_.month, datetime_.day,
                                          datetime_.hour, datetime_.minute,
                                          datetime_.second)

            return datetime_.strftime(date_format)

        return datetime_.strftime(date_format)
    # the localised date
    return localised_nice_date(datetime_,  with_hours=with_hours)


def _month_jan(day):
    return toolkit._('January {}').format(day)


def _month_feb(day):
    return toolkit._('February {}').format(day)


def _month_mar(day):
    return toolkit._('March {}').format(day)


def _month_apr(day):
    return toolkit._('April {}').format(day)


def _month_may(day):
    return toolkit._('May {}').format(day)


def _month_june(day):
    return toolkit._('June {}').format(day)


def _month_july(day):
    return toolkit._('July {}').format(day)


def _month_aug(day):
    return toolkit._('August {}').format(day)


def _month_sept(day):
    return toolkit._('September {}').format(day)


def _month_oct(day):
    return toolkit._('October {}').format(day)


def _month_nov(day):
    return toolkit._('November {}').format(day)


def _month_dec(day):
    return toolkit._('December {}').format(day)


_MONTH_FUNCTIONS = [_month_jan, _month_feb, _month_mar, _month_apr,
                   _month_may, _month_june, _month_july, _month_aug,
                   _month_sept, _month_oct, _month_nov, _month_dec]


def localised_nice_date(datetime_, with_hours=False):

    details = {
        'min': datetime_.minute,
        'hour': datetime_.hour,
        'month_day': _MONTH_FUNCTIONS[datetime_.month - 1](datetime_.day),
        'year': datetime_.year,
    }

    if with_hours:
        return toolkit._('{month_day}, {year}, {hour:02}:{min:02}').format(**details)
    else:
        return toolkit._('{month_day}, {year}').format(**details)
