import copy
import datetime
import re
from urlparse import urlparse

import ckan.plugins.toolkit as toolkit
from ckan import logic, model
from ckan.lib.helpers import check_access, map_pylons_to_flask_route_name, _link_active, _link_to, \
    _datestamp_to_datetime
from webhelpers.html import literal
from markupsafe import Markup, escape


def build_main(*args):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <div class="main-menu__item"><a href="...">title</a></div>
    '''
    output = ''
    l_start = '<div class="main-menu__item">'
    l_end = '</div>'
    for item in args:
        menu_item, title = item[:2]
        if len(item) == 3 and not check_access(item[2]):
            continue
        output += _make_menu_item(menu_item, title, l_start, l_end, l_start, l_end)
    return output


def build_nav_link(menu_item, title, **kw):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <div class="main-menu__item"><a href="...">title</a></div>
    '''
    l_start = ''
    l_end = ''

    return _make_menu_item(menu_item, title, l_start, l_end, l_start, l_end, **kw)


def get_tab_link(menu_item, title=None, img=None, **kw):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <div class="main-menu__item"><a href="...">title</a></div>
    '''

    return _make_menu_link(menu_item, title, icon=None, **kw)


def _make_menu_item(menu_item, title, literal_start, literal_end, literal_start_active, literal_end_active, **kw):
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
        return literal(literal_start_active) + link + literal(literal_end_active)
    return literal(literal_start) + link + literal(literal_end)


def _make_menu_link(menu_item, title, **kw):
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
    # link = _link_to(title, menu_item, **item)
    link = toolkit.url_for(menu_item, id=item['id'], action=item['action'], controller=item['controller'])
    return link


def get_tab(menu_item, title=None, img=None, **kw):
    ''' build a set of menu items.

    args: tuples of (menu type, title) eg ('login', _('Login'))
    outputs <div class="main-menu__item"><a href="...">title</a></div>
    '''
    link, active = _make_menu_tab(menu_item, title, **kw)
    img_lit = ''
    active_class = ''
    if img:
        img_lit = literal('<div class="custom-tab-header-item-icon"><img src="{}" alt="{}"></div>'.format(img, title))
    if active:
        active_class = ' custom-tab-header-item-active'

    return literal(u'<a class="custom-tab-header-item{}" href="{}">{}<div class="custom-tab-header-item-title">'
                   u'{}</div></a>'.format(active_class, link, img_lit, title))


def _make_menu_tab(menu_item, title, **kw):
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
    # link = _link_to(title, menu_item, **item)
    kwargs = {'action': item['action'], 'controller': item['controller']}
    if 'offset' in item:
        kwargs["offset"] = item['offset']
    if 'id' in item:
        kwargs["id"] = item['id']
    if 'resource_id' in item:
        kwargs["resource_id"] = item['resource_id']
    link = toolkit.url_for(menu_item, **kwargs)
    active = _link_active(item)

    return link, active


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


def recently_changed_packages_main(limit=5):
    if limit:
        data_dict = {'limit': limit}
    else:
        data_dict = {}
    context = {'model': model, 'session': model.Session, 'user': toolkit.c.user}
    package_list = logic.get_action('current_package_list_with_resources')(context, data_dict)

    return package_list


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


def mail_to_c(email_address, name):
    email = escape(email_address)
    author = escape(name)
    html = Markup(u'<a class=position-information-name href=mailto:{0}>{1}</a>'.format(email, author))
    return html


def clean_url(url):
    o = urlparse(url)
    url_without_query_string = o.netloc + o.path
    return url_without_query_string
