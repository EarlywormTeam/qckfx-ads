from toolbox.services.services import Services

class Toolbox:
    _services = None

    @property
    def services(self):
        if self._services is None:
            self._services = Services()
        return self._services
