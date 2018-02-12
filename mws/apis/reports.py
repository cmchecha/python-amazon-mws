"""
Amazon MWS Reports API
"""
from __future__ import absolute_import
import warnings

import mws
from .. import utils
from ..decorators import next_token_action


class Reports(mws.MWS):
    """
    Amazon MWS Reports API
    """
    ACCOUNT_TYPE = "Merchant"
    NEXT_TOKEN_OPERATIONS = [
        'GetReportRequestList',
        'GetReportScheduleList',
    ]

    # * REPORTS * #

    def get_report(self, report_id):
        data = dict(Action='GetReport', ReportId=report_id)
        return self.make_request(data)

    def get_report_count(self, report_types=(), acknowledged=None, fromdate=None, todate=None):
        data = dict(Action='GetReportCount',
                    Acknowledged=acknowledged,
                    AvailableFromDate=fromdate,
                    AvailableToDate=todate)
        data.update(utils.enumerate_param('ReportTypeList.Type.', report_types))
        return self.make_request(data)

    @next_token_action('GetReportList')
    def get_report_list(self, requestids=(), max_count=None, types=(), acknowledged=None,
                        fromdate=None, todate=None, next_token=None):
        data = dict(Action='GetReportList',
                    Acknowledged=acknowledged,
                    AvailableFromDate=fromdate,
                    AvailableToDate=todate,
                    MaxCount=max_count)
        data.update(utils.enumerate_param('ReportRequestIdList.Id.', requestids))
        data.update(utils.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)

    def get_report_list_by_next_token(self, token):
        """
        Deprecated.
        Use `get_report_list(next_token=token)` instead.
        """
        # data = dict(Action='GetReportListByNextToken', NextToken=token)
        # return self.make_request(data)
        warnings.warn(
            "Use `get_report_list(next_token=token)` instead.",
            DeprecationWarning,
        )
        return self.get_report_list(next_token=token)

    def get_report_request_count(self, report_types=(), processingstatuses=(),
                                 fromdate=None, todate=None):
        data = dict(Action='GetReportRequestCount',
                    RequestedFromDate=fromdate,
                    RequestedToDate=todate)
        data.update(utils.enumerate_param('ReportTypeList.Type.', report_types))
        data.update(utils.enumerate_param('ReportProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    @next_token_action('GetReportRequestList')
    def get_report_request_list(self, requestids=(), types=(), processingstatuses=(),
                                max_count=None, fromdate=None, todate=None, next_token=None):
        data = dict(Action='GetReportRequestList',
                    MaxCount=max_count,
                    RequestedFromDate=fromdate,
                    RequestedToDate=todate)
        data.update(utils.enumerate_param('ReportRequestIdList.Id.', requestids))
        data.update(utils.enumerate_param('ReportTypeList.Type.', types))
        data.update(utils.enumerate_param('ReportProcessingStatusList.Status.', processingstatuses))
        return self.make_request(data)

    def get_report_request_list_by_next_token(self, token):
        """
        Deprecated.
        Use `get_report_request_list(next_token=token)` instead.
        """
        # data = dict(Action='GetReportRequestListByNextToken', NextToken=token)
        # return self.make_request(data)
        warnings.warn(
            "Use `get_report_request_list(next_token=token)` instead.",
            DeprecationWarning,
        )
        return self.get_report_request_list(next_token=token)

    def request_report(self, report_type, start_date=None, end_date=None, marketplaceids=()):
        data = dict(Action='RequestReport',
                    ReportType=report_type,
                    StartDate=start_date,
                    EndDate=end_date)
        data.update(utils.enumerate_param('MarketplaceIdList.Id.', marketplaceids))
        return self.make_request(data)

    # * ReportSchedule * #

    def get_report_schedule_list(self, types=()):
        data = dict(Action='GetReportScheduleList')
        data.update(utils.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)

    def get_report_schedule_count(self, types=()):
        data = dict(Action='GetReportScheduleCount')
        data.update(utils.enumerate_param('ReportTypeList.Type.', types))
        return self.make_request(data)
