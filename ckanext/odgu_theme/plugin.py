# encoding: utf-8
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.odgu_theme import helpers

if toolkit.check_ckan_version(min_version='2.5'):
    from ckan.lib.plugins import DefaultTranslation

    class Odgu_ThemePluginBase(plugins.SingletonPlugin, DefaultTranslation):
        plugins.implements(plugins.ITranslation, inherit=True)
else:
    class IssuesPluginBase(p.SingletonPlugin):
        pass


class Odgu_ThemePlugin(Odgu_ThemePluginBase):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config):
        toolkit.add_template_directory(config, 'templates')
        toolkit.add_public_directory(config, 'public')
        toolkit.add_resource('fanstatic', 'static')

    def get_helpers(self):
        return {
            'build_main': helpers.build_main,
            'get_all_groups': helpers.get_all_groups,
            'recently_changed_packages_activity_stream_main': helpers.recently_changed_packages_activity_stream_main,
            'render_datetime_ukr': helpers.render_datetime_ukr,
        }

