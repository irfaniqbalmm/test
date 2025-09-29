
python3 -c 'import site; print(site.getsitepackages())'
/usr/lib/python3.6/site-packages/configobj.py

def _write_line(self, indent_string, entry, this_entry, comment):
        """Write an individual line, for the write method"""
        # NOTE: the calls to self._quote here handles non-StringType values.
        if not self.unrepr:
            #val = self._decode_element(self._quote(this_entry))
            val = this_entry
        else:
            val = repr(this_entry)
        return '%s%s%s%s%s' % (indent_string,
                               self._decode_element(self._quote(entry, multiline=False)),
                               self._a_to_u("="),
                               val,
                               self._decode_element(comment))

