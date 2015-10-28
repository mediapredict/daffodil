import operator as op



class DictionaryPredicateDelegate(object):
    def mk_any(self, children):
        return lambda data_point: any( predicate(data_point) for predicate in children)

    def mk_all(self, children):
        return lambda data_point: all( predicate(data_point) for predicate in children)

    def mk_not_any(self, children):
        return lambda data_point: not self.mk_any(children)(data_point)

    def mk_not_all(self, children):
        return lambda data_point: not self.mk_all(children)(data_point)

    def mk_test(self, test_str):
        ne = lambda *a: op.ne(*a)
        ne.onerror = True
        
        existance = lambda dp, k, v: (k in dp) == v
        existance.is_datapoint_test = True

        in_ = lambda a, b: a in b
        not_in_ = lambda a, b: not in_(a, b)

        ops = {
          '=':  op.eq,
          '!=': ne,
          '<':  op.lt,
          '<=': op.le,
          '>':  op.gt,
          '>=': op.ge,
          "?=": existance,
          "in": in_,
          "!in": not_in_,
        }
        return ops[test_str]

    def mk_cmp(self, key, val, test):
        if getattr(test, "is_datapoint_test", False):
            return lambda dp: test(dp, key, val)
        
        def test_data_point(data_point):
            cmp_val = val
            err_ret_val = getattr(test, "onerror", False)
            
            try: dp_val = data_point[key]
            except KeyError: return err_ret_val 
            
            # if only one value is a string try to coerce the string
            #   to the other value's type
            def coerce(val, fallback_type):
                try: return float(val)
                except: pass
                return fallback_type(val)

            def coerce_list(val, fallback_type):
                return [coerce(v, fallback_type) for v in val]
            

            if isinstance(cmp_val, list):
                cmp_val = coerce_list(cmp_val, type(dp_val))

            elif isinstance(cmp_val, basestring) != isinstance(dp_val, basestring):
                try:
                    if isinstance(cmp_val, basestring):
                        cmp_val = coerce(cmp_val, type(dp_val))
                    else:
                        dp_val = coerce(dp_val, type(cmp_val))
                except: return err_ret_val
                    
                
            try: return test(dp_val, cmp_val)
            except: pass
            
            try: return test(type(cmp_val)(data_point[key]), cmp_val)
            except: return err_ret_val
            
        return test_data_point

    def call(self, predicate, iterable):
        return filter(predicate, iterable)

