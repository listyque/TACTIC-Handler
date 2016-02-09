class Foo( object ):

    def foo( func ):

        def _foo( self, *args, **kwargs ):

            result = []
            result.append( func( self, *args, **kwargs ))
            return result

        return _foo

    def __init__( self ):

        self.obj = "test"

    @foo
    def result( self ):

        return self.obj

s = Foo()
s.result()