class AsyncCursorWrapper:
    def __init__(self, cursor):
        self._cursor = cursor

    def sort(self, *args, **kwargs):
        self._cursor = self._cursor.sort(*args, **kwargs)
        return self

    def limit(self, *args, **kwargs):
        self._cursor = self._cursor.limit(*args, **kwargs)
        return self

    def skip(self, *args, **kwargs):
        self._cursor = self._cursor.skip(*args, **kwargs)
        return self

    async def to_list(self, length=None):
        items = list(self._cursor)
        if length is not None:
            return items[:length]
        return items

    def __getattr__(self, name):
        return getattr(self._cursor, name)

class AsyncMockWrapper:
    def __init__(self, collection):
        self._collection = collection

    def __getattr__(self, name):
        attr = getattr(self._collection, name)
        if callable(attr):
            if name in ["find", "aggregate"]:
                def cursor_wrapper(*args, **kwargs):
                    return AsyncCursorWrapper(attr(*args, **kwargs))
                return cursor_wrapper
            
            async def async_wrapper(*args, **kwargs):
                return attr(*args, **kwargs)
            return async_wrapper
        return attr

class AsyncMockDB:
    def __init__(self, db):
        self._db = db
    
    def __getitem__(self, name):
        return AsyncMockWrapper(self._db[name])
    
    def __getattr__(self, name):
        return AsyncMockWrapper(getattr(self._db, name))
