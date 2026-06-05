class Singleton(type):
    _instances = {}

    def __call__(c, *args, **kwargs):
        if c not in c._instances:
            c._instances[c] = super().__call__(*args, **kwargs)

        return c._instances[c]
