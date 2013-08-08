import time

from path import path

from clld.tests.util import TestWithSelenium

import glottolog3


PROJECT = path(glottolog3.__file__).dirname().joinpath('..').abspath()


class Tests(TestWithSelenium):
    app = glottolog3.main(
        {'__file__': str(PROJECT.joinpath('development.ini')), 'here': str(PROJECT)},
        **{'sqlalchemy.url': 'postgres://robert@/glottolog3'})

    #def test_map(self):
    #    map_ = self.get_map('/contributions')
    #    map_.test_show_marker()
    #    map_.test_show_legend()
    #    map_.test_show_legend('lexifier')

    def test_datatable_family(self):
        dt = self.get_datatable('/glottolog/family')
        dt.filter('level', '--any--')
        self.assertEqual(dt.get_info().filtered, 4039)

    def test_datatable_language(self):
        dt = self.get_datatable('/glottolog/language')
        dt.filter('name', u'\xfc')
        self.assertEqual(dt.get_info().filtered, 2)