"""
Amazon MWS FulfillmentInboundShipment API
"""
from __future__ import absolute_import
# import warnings

from ..mws import MWS, MWSError
from .. import utils
from ..decorators import next_token_action


def parse_item_args(item_args, operation):
    """
    Parses item arguments sent to create_inbound_shipment_plan, create_inbound_shipment,
    and update_inbound_shipment methods.

    `item_args` is expected as an iterable containing dicts.
    Each dict should have the following keys:
        For `create_inbound_shipment_plan`:
        REQUIRED: 'sku', 'quantity'
        OPTIONAL: 'quantity_in_case', 'asin', 'condition'
        Other operations:
        REQUIRED: 'sku', 'quantity'
        OPTIONAL: 'quantity_in_case'
    If a required key is missing, throws MWSError.
    All extra keys are ignored.

    Keys (above) are converted to the appropriate MWS key according to `key_config` (below)
    based on the particular operation required.
    """
    if not item_args:
        raise MWSError("One or more `item` dict arguments required.")

    if operation == 'CreateInboundShipmentPlan':
        # `key_config` composed of list of tuples, each tuple compose of:
        # (input_key, output_key, is_required, default_value)
        key_config = [
            ('sku', 'SellerSKU', True, None),
            ('quantity', 'Quantity', True, None),
            ('quantity_in_case', 'QuantityInCase', False, None),
            ('asin', 'ASIN', False, None),
            ('condition', 'Condition', False, None),
        ]
        # The expected MWS key for quantity is different for this operation.
        # This ensures we use the right key later on.
        quantity_key = 'Quantity'
    else:
        key_config = [
            ('sku', 'SellerSKU', True, None),
            ('quantity', 'QuantityShipped', True, None),
            ('quantity_in_case', 'QuantityInCase', False, None),
        ]
        quantity_key = 'QuantityShipped'

    items = []
    for item in item_args:
        if not isinstance(item, dict):
            raise MWSError("`item` argument must be a dict.")
        if not all(k in item for k in [c[0] for c in key_config if c[2]]):
            # Required keys of an item line missing
            raise MWSError((
                "`item` dict missing required keys: {required}."
                "\n- Optional keys: {optional}."
            ).format(
                required=', '.join([c[0] for c in key_config if c[2]]),
                optional=', '.join([c[0] for c in key_config if not c[2]]),
            ))

        # Get data from the item.
        # Convert to str if present, or leave as None if missing
        quantity = item.get('quantity')
        if quantity is not None:
            quantity = str(quantity)

        quantity_in_case = item.get('quantity_in_case')
        if quantity_in_case is not None:
            quantity_in_case = str(quantity_in_case)

        item_dict = {
            'SellerSKU': item.get('sku'),
            quantity_key: quantity,
            'QuantityInCase': quantity_in_case,
        }
        item_dict.update({
            c[1]: item.get(c[0], c[3])
            for c in key_config
            if c[0] not in ['sku', 'quantity', 'quantity_in_case']
        })
        items.append(item_dict)

    return items


class InboundShipments(MWS):
    """
    Amazon MWS FulfillmentInboundShipment API
    """
    URI = "/FulfillmentInboundShipment/2010-10-01"
    VERSION = '2010-10-01'
    NAMESPACE = '{http://mws.amazonaws.com/FulfillmentInboundShipment/2010-10-01/}'
    NEXT_TOKEN_OPERATIONS = [
        'ListInboundShipments',
        'ListInboundShipmentItems',
    ]
    SHIPMENT_STATUSES = ['WORKING', 'SHIPPED', 'CANCELLED']
    DEFAULT_SHIP_STATUS = 'WORKING'
    LABEL_PREFERENCES = ['SELLER_LABEL',
                         'AMAZON_LABEL_ONLY',
                         'AMAZON_LABEL_PREFERRED']

    def __init__(self, *args, **kwargs):
        """
        Allow the addition of a from_address dict during object initialization.
        kwarg "from_address" is caught and popped here,
        then calls set_ship_from_address.
        If empty or left out, empty dict is set by default.
        """
        self.from_address = {}
        addr = kwargs.pop('from_address', None)
        if addr is not None:
            self.from_address = self.set_ship_from_address(addr)
        super(InboundShipments, self).__init__(*args, **kwargs)

    def set_ship_from_address(self, address):
        """
        Verifies the structure of an address dictionary.
        Once verified against the KEY_CONFIG, saves a parsed version
        of that dictionary, ready to send to requests.
        """
        # Clear existing
        self.from_address = None

        if not address:
            raise MWSError('Missing required `address` dict.')
        if not isinstance(address, dict):
            raise MWSError("`address` must be a dict")

        key_config = [
            # Tuples composed of:
            # (input_key, output_key, is_required, default_value)
            ('name', 'Name', True, None),
            ('address_1', 'AddressLine1', True, None),
            ('address_2', 'AddressLine2', False, None),
            ('city', 'City', True, None),
            ('district_or_county', 'DistrictOrCounty', False, None),
            ('state_or_province', 'StateOrProvinceCode', False, None),
            ('postal_code', 'PostalCode', False, None),
            ('country', 'CountryCode', False, 'US'),
        ]

        # Check if all REQUIRED keys in address exist:
        if not all(k in address for k in
                   [c[0] for c in key_config if c[2]]):
            # Required parts of address missing
            raise MWSError((
                "`address` dict missing required keys: {required}."
                "\n- Optional keys: {optional}."
            ).format(
                required=", ".join([c[0] for c in key_config if c[2]]),
                optional=", ".join([c[0] for c in key_config if not c[2]]),
            ))

        # Passed tests. Assign values
        addr = {'ShipFromAddress.{}'.format(c[1]): address.get(c[0], c[3])
                for c in key_config}
        self.from_address = addr

    def create_inbound_shipment_plan(self, items, country_code='US',
                                     subdivision_code='', label_preference=''):
        """
        Returns one or more inbound shipment plans, which provide the
        information you need to create inbound shipments.

        At least one dictionary must be passed as `args`. Each dictionary
        should contain the following keys:
          REQUIRED: 'sku', 'quantity'
          OPTIONAL: 'asin', 'condition', 'quantity_in_case'

        'from_address' is required. Call 'set_ship_from_address' first before
        using this operation.
        """
        if not items:
            raise MWSError("One or more `item` dict arguments required.")
        subdivision_code = subdivision_code or None
        label_preference = label_preference or None

        items = parse_item_args(items, 'CreateInboundShipmentPlan')
        if not self.from_address:
            raise MWSError((
                "ShipFromAddress has not been set. "
                "Please use `.set_ship_from_address()` first."
            ))

        data = dict(
            Action='CreateInboundShipmentPlan',
            ShipToCountryCode=country_code,
            ShipToCountrySubdivisionCode=subdivision_code,
            LabelPrepPreference=label_preference,
        )
        data.update(self.from_address)
        data.update(utils.enumerate_keyed_param(
            'InboundShipmentPlanRequestItems.member', items,
        ))
        return self.make_request(data, method="POST")

    def create_inbound_shipment(self, shipment_id, shipment_name,
                                destination, items, shipment_status='',
                                label_preference='', case_required=False,
                                box_contents_source=None):
        """
        Creates an inbound shipment to Amazon's fulfillment network.

        At least one dictionary must be passed as `items`. Each dictionary
        should contain the following keys:
          REQUIRED: 'sku', 'quantity'
          OPTIONAL: 'quantity_in_case'

        'from_address' is required. Call 'set_ship_from_address' first before
        using this operation.
        """
        assert isinstance(shipment_id, str), "`shipment_id` must be a string."
        assert isinstance(shipment_name, str), "`shipment_name` must be a string."
        assert isinstance(destination, str), "`destination` must be a string."

        if not items:
            raise MWSError("One or more `item` dict arguments required.")

        items = parse_item_args(items, 'CreateInboundShipment')

        if not self.from_address:
            raise MWSError((
                "ShipFromAddress has not been set. "
                "Please use `.set_ship_from_address()` first."
            ))
        from_address = self.from_address
        from_address = {'InboundShipmentHeader.{}'.format(k): v
                        for k, v in from_address.items()}

        if shipment_status not in self.SHIPMENT_STATUSES:
            # Status is required for `create` request.
            # Set it to default.
            shipment_status = self.DEFAULT_SHIP_STATUS

        if label_preference not in self.LABEL_PREFERENCES:
            # Label preference not required. Set to None
            label_preference = None

        # Explict True/False for case_required,
        # written as the strings MWS expects.
        case_required = 'true' if case_required else 'false'

        data = {
            'Action': 'CreateInboundShipment',
            'ShipmentId': shipment_id,
            'InboundShipmentHeader.ShipmentName': shipment_name,
            'InboundShipmentHeader.DestinationFulfillmentCenterId': destination,
            'InboundShipmentHeader.LabelPrepPreference': label_preference,
            'InboundShipmentHeader.AreCasesRequired': case_required,
            'InboundShipmentHeader.ShipmentStatus': shipment_status,
            'InboundShipmentHeader.IntendedBoxContentsSource': box_contents_source,
        }
        data.update(from_address)
        data.update(utils.enumerate_keyed_param(
            'InboundShipmentItems.member', items,
        ))
        return self.make_request(data, method="POST")

    def update_inbound_shipment(self, shipment_id, shipment_name,
                                destination, items=None, shipment_status='',
                                label_preference='', case_required=False,
                                box_contents_source=None):
        """
        Updates an existing inbound shipment in Amazon FBA.
        'from_address' is required. Call 'set_ship_from_address' first before
        using this operation.
        """
        # Assert these are strings, error out if not.
        assert isinstance(shipment_id, str), "`shipment_id` must be a string."
        assert isinstance(shipment_name, str), "`shipment_name` must be a string."
        assert isinstance(destination, str), "`destination` must be a string."

        # Parse item args
        if items:
            items = parse_item_args(items, 'UpdateInboundShipment')
        else:
            items = None

        # Raise exception if no from_address has been set prior to calling
        if not self.from_address:
            raise MWSError((
                "ShipFromAddress has not been set. "
                "Please use `.set_ship_from_address()` first."
            ))
        # Assemble the from_address using operation-specific header
        from_address = self.from_address
        from_address = {'InboundShipmentHeader.{}'.format(k): v
                        for k, v in from_address.items()}

        if shipment_status not in self.SHIPMENT_STATUSES:
            # Passed shipment status is an invalid choice.
            # Remove it from this request by setting it to None.
            shipment_status = None

        if label_preference not in self.LABEL_PREFERENCES:
            # Passed label preference is an invalid choice.
            # Remove it from this request by setting it to None.
            label_preference = None

        case_required = 'true' if case_required else 'false'

        data = {
            'Action': 'UpdateInboundShipment',
            'ShipmentId': shipment_id,
            'InboundShipmentHeader.ShipmentName': shipment_name,
            'InboundShipmentHeader.DestinationFulfillmentCenterId': destination,
            'InboundShipmentHeader.LabelPrepPreference': label_preference,
            'InboundShipmentHeader.AreCasesRequired': case_required,
            'InboundShipmentHeader.ShipmentStatus': shipment_status,
            'InboundShipmentHeader.IntendedBoxContentsSource': box_contents_source,
        }
        data.update(from_address)
        if items:
            # Update with an items paramater only if they exist.
            data.update(utils.enumerate_keyed_param(
                'InboundShipmentItems.member', items,
            ))
        return self.make_request(data, method="POST")

    def get_prep_instructions_for_sku(self, skus=None, country_code=None):
        """
        Returns labeling requirements and item preparation instructions
        to help you prepare items for an inbound shipment.
        """
        country_code = country_code or 'US'
        skus = skus or []

        # 'skus' should be a unique list, or there may be an error returned.
        skus = utils.unique_list_order_preserved(skus)

        data = dict(
            Action='GetPrepInstructionsForSKU',
            ShipToCountryCode=country_code,
        )
        data.update(utils.enumerate_params({
            'SellerSKUList.ID.': skus,
        }))
        return self.make_request(data, method="POST")

    def get_prep_instructions_for_asin(self, asins=None, country_code=None):
        """
        Returns item preparation instructions to help with
        item sourcing decisions.
        """
        country_code = country_code or 'US'
        asins = asins or []

        # 'asins' should be a unique list, or there may be an error returned.
        asins = utils.unique_list_order_preserved(asins)

        data = dict(
            Action='GetPrepInstructionsForASIN',
            ShipToCountryCode=country_code,
        )
        data.update(utils.enumerate_params({
            'ASINList.ID.': asins,
        }))
        return self.make_request(data, method="POST")

    def get_package_labels(self, shipment_id, num_packages, page_type=None):
        """
        Returns PDF document data for printing package labels for
        an inbound shipment.
        """
        data = dict(
            Action='GetPackageLabels',
            ShipmentId=shipment_id,
            PageType=page_type,
            NumberOfPackages=str(num_packages),
        )
        return self.make_request(data, method="POST")

    def get_transport_content(self, shipment_id):
        """
        Returns current transportation information about an
        inbound shipment.
        """
        data = dict(
            Action='GetTransportContent',
            ShipmentId=shipment_id
        )
        return self.make_request(data, method="POST")

    def estimate_transport_request(self, shipment_id):
        """
        Requests an estimate of the shipping cost for an inbound shipment.
        """
        data = dict(
            Action='EstimateTransportRequest',
            ShipmentId=shipment_id,
        )
        return self.make_request(data, method="POST")

    def void_transport_request(self, shipment_id):
        """
        Voids a previously-confirmed request to ship your inbound shipment
        using an Amazon-partnered carrier.
        """
        data = dict(
            Action='VoidTransportRequest',
            ShipmentId=shipment_id
        )
        return self.make_request(data, method="POST")

    def get_bill_of_lading(self, shipment_id):
        """
        Returns PDF document data for printing a bill of lading
        for an inbound shipment.
        """
        data = dict(
            Action='GetBillOfLading',
            ShipmentId=shipment_id,
        )
        return self.make_request(data, "POST")

    @next_token_action('ListInboundShipments')
    def list_inbound_shipments(self, shipment_ids=None, shipment_statuses=None,
                               last_updated_after=None, last_updated_before=None,):
        """
        Returns list of shipments based on statuses, IDs, and/or
        before/after datetimes.
        """
        last_updated_after = utils.dt_iso_or_none(last_updated_after)
        last_updated_before = utils.dt_iso_or_none(last_updated_before)

        data = dict(
            Action='ListInboundShipments',
            LastUpdatedAfter=last_updated_after,
            LastUpdatedBefore=last_updated_before,
        )
        data.update(utils.enumerate_params({
            'ShipmentStatusList.member.': shipment_statuses,
            'ShipmentIdList.member.': shipment_ids,
        }))
        return self.make_request(data, method="POST")

    @next_token_action('ListInboundShipmentItems')
    def list_inbound_shipment_items(self, shipment_id=None, last_updated_after=None,
                                    last_updated_before=None,):
        """
        Returns list of items within inbound shipments and/or
        before/after datetimes.
        """
        last_updated_after = utils.dt_iso_or_none(last_updated_after)
        last_updated_before = utils.dt_iso_or_none(last_updated_before)

        data = dict(
            Action='ListInboundShipmentItems',
            ShipmentId=shipment_id,
            LastUpdatedAfter=last_updated_after,
            LastUpdatedBefore=last_updated_before,
        )
        return self.make_request(data, method="POST")
