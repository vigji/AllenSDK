# Copyright 2014 Allen Institute for Brain Science
# This file is part of Allen SDK.
#
# Allen SDK is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Allen SDK is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Allen SDK.  If not, see <http://www.gnu.org/licenses/>.

import logging

from allensdk.config.model.manifest import Manifest


class Description(object):
    _log = logging.getLogger(__name__)
    
    def __init__(self):
        self.data = {}
        self.reserved_data = []
        self.manifest = Manifest()
    
    
    def update_data(self, data):
        self.data.update(data)
    
    
    def is_empty(self):
        if self.data:
            return False
        
        return True
    
    
    def unpack(self, data):
        self.unpack_manifest(data)
        self.update_data(data)
    
    
    def unpack_manifest(self, data):
        data_manifest = data.pop("manifest", {})
        reserved_data = { "manifest": data_manifest }
        self.reserved_data.append(reserved_data)
        self.manifest.load_config(data_manifest)
    
    
    def fix_unary_sections(self, section_names=None):
        ''' Wrap section contents that don't have the proper
            array surrounding them in an array.
        '''
        if section_names is None:
            section_names = []
        
        for section in section_names:
            if section in self.data:
                if type(self.data[section]) is dict:
                    self.data[section] = [ self.data[section] ];
                    Description._log.warn("wrapped description section %s in an array." % (section))

