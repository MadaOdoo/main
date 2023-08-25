from odoo import models, fields


class ShopifySync(models.Model):
    _name = 'shopify.sync'
    _description = 'Shopify Sync'

    product_id = fields.Many2one('product.template')
    product_prod_id = fields.Many2one('product.product')
    customer_id = fields.Many2one('res.partner')
    order_id = fields.Many2one('sale.order')
    instance_id = fields.Many2one('shopify.configuration',
                                  string="Instance")
    shopify_product_id = fields.Char('Product Id')
    shopify_customer_id = fields.Char('Customer Id')
    shopify_order_id = fields.Char('Order Id')
    synced_order = fields.Boolean(readonly=True, store=True)
    shopify_order_name = fields.Char('Name', readonly=True,
                                     store=True)
    shopify_order_number = fields.Char('Order No', readonly=True,
                                       store=True)
    payment_status = fields.Selection([('paid', 'Paid'),
                                       ('partially_paid', 'Partially Paid'),
                                       ('unpaid', 'Unpaid'),
                                       ('refunded', 'Refunded'),
                                       ('partially_refunded',
                                        'Partially Refunded')],
                                      string='Payment Status',
                                      default='unpaid', readonly=True,
                                      store=True)
    fulfillment_status = fields.Selection([('fulfilled', 'Fulfilled'),
                                           ('partially_fulfilled',
                                            'Partially Fulfiled'),
                                           ('un_fulfilled', 'Un Fulfilled')],
                                          string='Fulfillment Status',
                                          default='un_fulfilled',
                                          readonly=True, store=True)
    order_status = fields.Selection([('open', 'Open'),
                                     ('completed', 'Completed')],
                                    string='Order Status',
                                    default='open', readonly=True,
                                    store=True)
    last_order_id = fields.Char('Last order id', readonly=True,
                                store=True)
