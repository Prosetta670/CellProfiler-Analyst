#!/usr/bin/env python

from Singleton import *

# TODO: check type of all field values
string_vars = ['db_type', 'db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                'image_table', 'object_table',
                'image_csv_file', 'object_csv_file',
                'table_id', 'image_id', 'object_id', 'plate_id', 'well_id',
                'cell_x_loc', 'cell_y_loc',
                'image_url_prepend',
                'image_tile_size', 'image_buffer_size',
                'tile_buffer_size',
                'area_scoring_column',
                'training_set',
                'plate_type']

list_vars = ['image_channel_paths', 'image_channel_files', 'image_channel_names', 'image_channel_colors',
            'object_name',
            'classifier_ignore_substrings']


class Properties(Singleton):
    '''
    Loads and stores properties files.
    '''
    def __init__(self):
        super(Properties, self).__init__()        
    
    def __str__(self):
        s=''
        for k, v in self.__dict__.items():
            if not str(k).startswith('_'):
                s += k+" = "+str(v)+"\n"
        return s
        
    
    def __getattr__(self, field):
        # The name may not be loaded for optional fields.
        if not self.__dict__.has_key(field):
            return None
        else:
            return self.__dict__[field]
        
    
    def __setattr__(self, id, val):
        self.__dict__[id] = val
    
    
    def LoadFile(self, filename):
        ''' Loads variables in from a properties file. '''
        self.Clear()
        self._filename = filename
        f = open(filename, 'U')
        
        lines = f.read()
        self._textfile = lines
#        lines = lines.replace('\r', '\n')                        # replace CRs with LFs
        lines = lines.split('\n')

        self._groups = {}
        self._groups_ordered = []
        self._filters = {}
        self._filters_ordered = []

        for line in lines:
            if not line.strip().startswith('#') and line.strip()!='':          # skip commented and empty lines
                (name, val) = line.split('=', 1)                               # split each side of the first eq sign
                name = name.strip()
                val = val.strip()
                
                if name in string_vars:
                    self.__dict__[name] = val
                
                elif name in list_vars:
                    self.__dict__[name] = [v.strip() for v in val.split(',') if v.strip() is not '']
                    
                elif name.startswith('group_SQL_'):
                    group_name = name[10:]
                    if group_name == '':
                        raise Exception, 'PROPERTIES ERROR (%s): "group_SQL_" should be followed by a group name.\nExample: "group_SQL_MyGroup = <QUERY>" would define a group named "MyGroup" defined by\na MySQL query "<QUERY>". See the README.'%(name)
                    if group_name in self._groups.keys():
                        raise Exception, 'Group "%s" is defined twice in properties file.'%(group_name)
                    if group_name in self._filters.keys():
                        raise Exception, 'Name "%s" is already taken for a filter.'%(group_name)
                    if not val:
                        print 'PROPERTIES WARNING (%s): Undefined group'%(name)
                        continue
                    # TODO: test query
                    self._groups[group_name] = val
                    self._groups_ordered += [group_name]
                    
                elif name.startswith('filter_SQL_'):
                    filter_name = name[11:]
                    if filter_name == '':
                        raise Exception, 'PROPERTIES ERROR (%s): "filter_SQL_" should be followed by a filter name.\nExample: "filter_SQL_MyFilter = <QUERY>" would define a filter named "MyFilter" defined by\na MySQL query "<QUERY>". See the README.'%(name)
                    if filter_name in self._filters.keys():
                        raise Exception, 'Filter "%s" is defined twice in properties file.'%(filter_name)
                    if filter_name in self._groups.keys():
                        raise Exception, 'Name "%s" is already taken for a group.'%(filter_name)
                    if not val:
                        print 'PROPERTIES WARNING (%s): Undefined filter'%(name)
                        continue
                    # TODO: test query
                    self._filters[filter_name] = val
                    self._filters_ordered += [filter_name]
                
                elif name in ['groups', 'filters']:
                    print 'PROPERTIES WARNING (%s): This field is no longer necessary in the properties file.\nOnly the group_SQL_XXX and filter_SQL_XXX fields are needed when defining groups and filters.'%(name)
                    
                else:
                    print 'PROPERTIES WARNING: Unrecognized field "%s" in properties file'%(name)
                
        f.close()
        self.Validate()
        
    
    def SaveFile(self, filename):
        ''' Saves the file including original comments and whitespace. '''
        f = open(filename, 'w')
        self._filename = filename
        
        fields_to_write = set([f for f in self.__dict__.keys() if not f.startswith('_')])
        
        # Write whole file out replacing any changed values
        for line in self._textfile:
            if line.strip().startswith('#'):
                f.write(line)
            else:
                (name, oldval) = line.split('=', 1)                               # split each side of the first eq sign
                name = name.strip()
                oldval = oldval.strip()
                val = self.__getattr__(name)
                if (name in string_vars and val == oldval) or \
                   (name in list_vars and val == [v.strip() for v in oldval.split(',') if v.strip() is not '']):
                    f.write(line)
                else:
                    f.write('%s  =  %s\n'%(name, val))
                fields_to_write.remove(name)
        
        # Write out fields that weren't present in the file
        for field in fields_to_write:
            val = self.__getattr__(field)
            if type(val)==list:
                f.write('%s  =  %s\n'%(field, str(val)[1:-1]))
            else:
                f.write('%s  =  %s\n'%(field, val))
        
        f.close()
        
    
    def Clear(self):
        self.__dict__ = {}
        
        
    def IsEmpty(self):
        return self.__dict__ == {}


    def Validate(self):
        
        def field_defined(name):
            # field name exists and has a non-empty value.
            return name in self.__dict__.keys() and self.__dict__[name]!=''

        # Check that all required variables were loaded
        optional_vars = ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',
                         'table_id', 'image_url_prepend', 'image_csv_file',
                         'image_channel_names', 'image_channel_colors',
                         'object_csv_file', 'area_scoring_column', 'training_set',
                         'image_buffer_size', 'tile_buffer_size',
                         'plate_id', 'well_id', 'plate_type']
        
        # check that all required fields are defined
        for name in string_vars + list_vars:
            if name not in optional_vars:
                assert field_defined(name), 'PROPERTIES ERROR (%s): Field is missing or empty.'%(name)        
        
        assert self.db_type.lower() in ['mysql', 'sqlite'], 'PROPERTIES ERROR (db_type): Value must be either "mysql" or "sqlite".'
        
        # BELOW: Check sometimes-optional fields, and print warnings etc
        if self.db_type.lower()=='sqlite':
            for field in ['db_port', 'db_host', 'db_name', 'db_user', 'db_passwd',]:
                if field_defined(field):
                    print 'PROPERTIES WARNING (%s): Field not required with db_type=sqlite.'%(field)
            for field in ['image_csv_file','object_csv_file']:
                assert field_defined(field), 'PROPERTIES ERROR (%s): Field is required with db_type=sqlite.'%(field)
                try:
                    f = open(self.__dict__[field], 'r')
                    f.close()
                except:
                    raise Exception, 'PROPERTIES ERROR (%s): File "%s" could not be found.'%(field, self.__dict__[field])                
            
        if self.db_type.lower()=='mysql':
            for field in ['db_port', 'db_host', 'db_name', 'db_user',]:
                assert field_defined(field), 'PROPERTIES ERROR (%s): Field is required with db_type=mysql.'%(field)
            for field in ['image_csv_file','object_csv_file']:
                if field_defined(field):
                    print 'PROPERTIES WARNING (%s): Field not required with db_type=mysql.'%(field)
        
        if field_defined('area_scoring_column'):
            print 'PROPERTIES: Area scoring will be used.'
        
        if not field_defined('image_channel_names'):
            print 'PROPERTIES WARNING (image_channel_names): No value(s) specified. Classifier will use generic channel names.'
            self.image_channel_names = ['channel-%d'%(i) for i in range(103)] [:len(self.image_channel_files)]

        if not field_defined('image_channel_colors'):
            print 'PROPERTIES WARNING (image_channel_colors): No value(s) specified. Classifier will use a generic channel-color mapping.'
            self.image_channel_colors = ['red', 'green', 'blue']+['none' for x in range(100)] [:len(self.image_channel_files)]

        if not field_defined('classifier_ignore_substrings'):
            print 'PROPERTIES WARNING (classifier_ignore_substrings): No value(s) specified. Classifier will use ALL NUMERIC per_object columns when training.'
        
        if not field_defined('image_buffer_size'):
            print 'PROPERTIES: Using default image_buffer_size=1'
            self.image_buffer_size = 1
            
        if not field_defined('tile_buffer_size'):
            print 'PROPERTIES: Using default tile_buffer_size=1'
            self.tile_buffer_size = 1
            
        if not field_defined('object_name'):
            print 'PROPERTIES WARNING (object_name): No object name specified, will use default: "object_name=cell,cells"'
            self.object_name = ['cell', 'cells']
        else:
            # if it is defined make sure they do it correctly
            assert len(self.object_name)==2, 'PROPERTIES ERROR (object_name): Found %d names instead of 2! This field should contain the singular and plural name of the objects you are classifying. (Example: object_name=cell,cells)'%(len(self.object_name))

        if field_defined('training_set'):
            try:
                f = open(self.training_set)
                f.close()
            except:
                print 'PROPERTIES WARNING (training_set): Training set at "%s" could not be found.'%(self.training_set)                        
            print 'PROPERTIES: Training set found at "%s"'%(self.training_set)
            
        if not field_defined('plate_id'):
            print 'PROPERTIES WARNING (plate_id): Field is required for plate map viewer.'
                                    
        if not field_defined('well_id'):
            print 'PROPERTIES WARNING (well_id): Field is required for plate map viewer.'
                                    
        if not field_defined('plate_type'):
            print 'PROPERTIES WARNING (plate_type): Field is required for plate map viewer.'                        

        
if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        filename = "../Properties/nirht_area_test.properties"
    
    p = Properties.getInstance()
    p.LoadFile(filename)
    print p

