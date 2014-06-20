from django.db import Q


class HStoreQueryDelegate(object):
    def mk_any(self, children):
    	q = Q()
    	for child_q in children:
    		q |= child_q
        return q

    def mk_all(self, children):
        q = Q()
    	for child_q in children:
    		q &= child_q
        return q

    def mk_test(self, test_str):
        return

    def mk_cmp(self, key, val, test):
        return