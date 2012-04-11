'''
Created on Mar 31, 2012

@author: quandtan
'''

from applicake.utils.sequenceutils import SequenceUtils


class DictUtils(SequenceUtils):
    """
    Utilities for handling dictionaries
    """
    
    @staticmethod
    def extract(dictionary,keys):
        """
        Extract subset of a dictionary based on a list of keys
        
        Arguments:
        - dictionary: The original dictionary
        - keys: Keys used to create the subset
        
        Return: Dictionary containing the subset
        """
        return dict((key, dictionary[key]) for key in keys if key in dictionary)
    
    @staticmethod  
    def merge(dict_1, dict_2, priority='left'):
        """
        Merging of 2 dictionaries
        
        Arguments:
        - dict_1: first dictionary
        - dict_2: second dictionary
        - priority: priority of the merging
        -- left: First dictionary overwrites existing keys in second dictionary
        -- right: Second dictionary overwrites existing keys in first dictionary
        -- equal: Keys with same values are not changed. 
            Keys with different values are merged into lists where the value of 
            dict_1 is first in the list.
            Keys that only exist in one dictionary are added
        
        Return: merged dictionary
        """
        d1 = dict_1.copy()
        d2 = dict_2.copy()
        if priority == 'left':     
            return dict(d2,**d1)
        elif priority == 'right':     
            return dict(d1,**d2)  
        elif priority == 'flatten_sequence':
            for k,v in d2.iteritems():
                if k in d1.keys():
                    if d1[k] != d2[k]:                        
                        sequence = [d1[k],d2[k]]
                        d1[k] = DictUtils.get_flatten_sequence(sequence)
                else:
                    d1[k]=v
            return d1
        
    @staticmethod
    def remove_none_entries(dictionary):
        """
        Removes key/value pairs where the value is None
        
        Input:
        - dictionary 
        
        Return: Copy of the input dictionary where the None key/values are removed
        """
        copied_dict  = dictionary.copy()
        keys = []
        for k,v in copied_dict.iteritems():
            if v is None:
                keys.append(k)
        for k in keys:
            copied_dict.pop(k)
        return copied_dict           