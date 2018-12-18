from scrapy.dupefilter import RFPDupeFilter

class CustomFilter(RFPDupeFilter):
    def request_seen(self, request):
        return False