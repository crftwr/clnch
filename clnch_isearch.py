import sys
import os
import re
import fnmatch

import ckit

import clnch_ini

migemo_object = None

class IncrementalSearch:

    def __init__( self ):
        self.isearch_value = ""
        self.isearch_type = clnch_ini.get( "MISC", "isearch_type", "partial" ) 
        self.migemo_pattern = None
        self.migemo_re_pattern = ""
        self.migemo_re_object = None
        self.migemo_re_result = None

    def fnmatch( self, name, pattern, isearch_type=None ):
    
        global migemo_object

        if isearch_type==None:
            isearch_type=self.isearch_type

        # migemoは大文字小文字が混在しているときだけ有効
        if isearch_type=="migemo":
            if pattern.lower()==pattern:
                isearch_type="partial"

        if isearch_type=="partial":
            return fnmatch.fnmatch( name, '*'+pattern+'*' )

        elif isearch_type=="inaccurate":
            new_pattern = "*"
            for ch in pattern:
                new_pattern += ch + "*"
            return fnmatch.fnmatch( name, new_pattern )

        elif isearch_type=="migemo":

            # 初めて migemo が必要になったときに遅延ロードする                    
            if migemo_object==None:
                dll_path = os.path.join( ckit.getAppExePath(), 'lib' )
                dict_path = os.path.join( ckit.getAppExePath(), 'dict' )
                migemo_object = ckit.Migemo( dll_path, dict_path )
            
            # 検索パターンが変更になったときだけクエリーをかける
            if self.migemo_pattern != pattern:
                
                re_pattern = migemo_object.query(pattern)
                
                try:
                    self.migemo_re_object = re.compile( re_pattern, re.IGNORECASE )
                except Exception as e:
                    # FIXME:
                    # migemo_re_pattern のなかに | や + などの正規表現の特殊文字が入っていたときはエラーになってしまう。
                    # 例外が発生したときに True を返すことで無理やり対応するが、正しい対応方法を模索する。
                    if 0:
                        print( "正規表現のエラー :", e )
                    return True

                self.migemo_pattern = pattern
                self.migemo_re_pattern = re_pattern
            
            re_result = self.migemo_re_object.search(name)
            if re_result:
                self.migemo_re_result = re_result
            return re_result!=None

        else:
            return fnmatch.fnmatch( name, pattern+'*' )

    def cursorUp( self, get_string, length, select, scroll_pos, visible_height, margin=0 ):
        for i in range( select-1, -1, -1 ):
            if self.fnmatch( get_string(i), self.isearch_value ):
                select = i
                break
        return select

    def cursorDown( self, get_string, length, select, scroll_pos, visible_height, margin=0 ):
        for i in range( select+1, length ):
            if self.fnmatch( get_string(i), self.isearch_value ):
                select = i
                break
        return select

    def cursorPageUp( self, get_string, length, select, scroll_pos, visible_height, margin=0 ):

        last_found = -1

        for begin, end in ( ( select-1, scroll_pos-1+margin ), ( scroll_pos-1, scroll_pos-1-visible_height++margin ) ):

            for i in range( begin, max(end,-1), -1 ):
                if self.fnmatch( get_string(i), self.isearch_value ):
                    last_found = i

            if last_found!=-1:
                break

        if last_found==-1:
            return self.cursorUp( get_string, length, select, scroll_pos, visible_height, margin )
        
        return last_found

    def cursorPageDown( self, get_string, length, select, scroll_pos, visible_height, margin=0 ):

        last_found = -1

        for begin, end in ( ( select+1, scroll_pos+visible_height-margin ), ( scroll_pos+visible_height, scroll_pos+visible_height+visible_height-margin ) ):

            for i in range( begin, min(end,length) ):
                if self.fnmatch( get_string(i), self.isearch_value ):
                    last_found = i

            if last_found!=-1:
                break

        if last_found==-1:
            return self.cursorDown( get_string, length, select, scroll_pos, visible_height, margin )

        return last_found

