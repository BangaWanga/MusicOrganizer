import typing
import uuid


class PageLink:
    def __init__(self):
        self._link_id = uuid.uuid4()

    @property
    def link_id(self):
        return self._link_id


class Page:
    def __init__(self, value: typing.Any):
        self.value = value
        self.page_link = PageLink()


class PageContainer(Page):
    def __init__(self, value: list):    # ToDo: Maybe allow iterable
        super().__init__(value=value)

    def append(self, new_val):
        self.value.append(new_val)


class ObservedPage(PageContainer):
    def __init__(self):
        super().__init__([])
        self.subscribers: list[PageLink] = []
        """
        Observes changes made for value. Informs subscribed pages to update
        """

    @staticmethod
    def _observed(func: typing.Callable):
        def _observer(cls, new_val):
            print("Calling function with args ", cls, new_val)
            func(cls, new_val)
            print("After calling function")
        return _observer

    @_observed
    def append(self, new_val):
        super().append(new_val)


if __name__ == "__main__":
    myList = ObservedPage()
    myList.append(1)