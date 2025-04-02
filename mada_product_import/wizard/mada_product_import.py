# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import os
from base64 import b64decode

from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import xlrd
    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class MaraProductImport(models.TransientModel):
    _name = "mara.product.import"
    _description = "Mara Product Import"

    def _read_xls(self, options):
        book = xlrd.open_workbook(file_contents=b64decode(self.file) or b'')
        sheets = options['sheets'] = book.sheet_names()
        sheet = options['sheet'] = options.get('sheet') or sheets[0]
        return self._read_xls_book(book, sheet)

    def _read_xls_book(self, book, sheet_name):
        sheet = book.sheet_by_name(sheet_name)
        rows = []
        # emulate Sheet.get_rows for pre-0.9.4
        for rowx, row in enumerate(map(sheet.row, range(sheet.nrows)), 1):
            values = []
            for colx, cell in enumerate(row, 1):
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        str(cell.value)
                        if is_float
                        else str(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    # emulate xldate_as_datetime for pre-0.9.3
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                elif cell.ctype is xlrd.XL_CELL_ERROR:
                    raise ValueError(
                        _("Invalid cell value at row %(row)s, column %(col)s: %(cell_value)s") % {
                            'row': rowx,
                            'col': colx,
                            'cell_value': xlrd.error_text_from_code.get(cell.value, _("unknown error code %s", cell.value))
                        }
                    )
                else:
                    values.append(cell.value)
            if any(x for x in values if x.strip()):
                rows.append(values)

        # return the file length as first value
        return sheet.nrows, rows

    file = fields.Binary('File', required=True, attachment=False)
    filename = fields.Char('File Name', required=True)
    import_log = fields.Text(string="Log")

    def product_import(self):
        ProductAttribute = self.env['product.attribute']
        ProductAttributeValue = self.env['product.attribute.value']
        PTAttributeLine = self.env['product.template.attribute.line']
        PTAttributeValue = self.env['product.template.attribute.value']

        if self.import_log:
            return {}
        fileformat = os.path.splitext(self.filename)[-1][1:].lower()
        if fileformat not in ('xls','xlsx'):
            raise UserError(_('Valid format is .xls or .xlsx'))

        file_length, rows = self._read_xls({})
        rows = rows[1:]
        attr_color = ProductAttribute.search([('name', '=ilike', 'Color Principal')], limit=1) or ProductAttribute.create({'name': 'Color Principal'})
        attr_talla = ProductAttribute.search([('name', '=ilike', 'Talla')], limit=1) or ProductAttribute.create({'name': 'Talla'})
        template_list = []

        for row in rows:
            categ = self.env['product.category'].search([('name', '=ilike', row[3])], limit=1) \
                or self.env['product.category'].create({'name': row[3]})

            template = self.env['product.template'].search([('name', '=ilike', row[1])], limit=1)
            if not template:
                tags = row[4].split(",")
                tag_ids = []
                for tag in tags:
                    _tag = self.env['product.tag'].search([('name', '=ilike', tag)], limit=1) or self.env['product.tag'].create({'name': tag})
                    tag_ids.append(_tag.id)

                template_values = {
                    'name': row[1],
                    'detailed_type': 'product',
                    'categ_id': categ.id,
                    'list_price': float(row[9]),
                    'product_tag_ids': [(6, 0, tag_ids)]
                }
                supplier = self.env['res.partner'].search([('name', '=ilike', row[2])], limit=1) #\
                #    or self.env['res.partner'].create({'name': row[2]})
                if supplier:
                    template_values.update({'seller_ids': [(0, 0, {'partner_id':supplier.id})]})
                template = self.env['product.template'].create(template_values)

            template_list.append(template.id)
            attr_color_value = ProductAttributeValue.search([('name', '=ilike', row[5]),('attribute_id', '=', attr_color.id)], limit=1) \
                or ProductAttributeValue.create({'name': row[5], 'attribute_id':attr_color.id})

            attr_talla_value = ProductAttributeValue.search([('name', '=ilike', row[6]),('attribute_id', '=', attr_talla.id)], limit=1) \
                or ProductAttributeValue.create({'name': row[6], 'attribute_id':attr_talla.id})

            pt_attr_line_color = PTAttributeLine.search([('product_tmpl_id', '=', template.id),('attribute_id', '=', attr_color.id)], limit=1) \
                or PTAttributeLine.create({'product_tmpl_id': template.id, 'attribute_id': attr_color.id, 'value_ids': [(6, 0, [attr_color_value.id])]})
            pt_attr_line_color.write({'value_ids': [(4, attr_color_value.id)]})

            pt_attr_line_talla = PTAttributeLine.search([('product_tmpl_id', '=', template.id),('attribute_id', '=', attr_talla.id)], limit=1) \
                or PTAttributeLine.create({'product_tmpl_id': template.id, 'attribute_id': attr_talla.id, 'value_ids': [(6, 0, [attr_talla_value.id])]})
            pt_attr_line_talla.write({'value_ids': [(4, attr_talla_value.id)]})

            pt_attr_value_color = PTAttributeValue.search([('product_tmpl_id', '=', template.id),('attribute_line_id', '=', pt_attr_line_color.id),('product_attribute_value_id', '=', attr_color_value.id)])
            pt_attr_value_talla = PTAttributeValue.search([('product_tmpl_id', '=', template.id),('attribute_line_id', '=', pt_attr_line_talla.id),('product_attribute_value_id', '=', attr_talla_value.id)])

            product = self.env['product.product'].search([
                ('product_tmpl_id', '=', template.id),
                ('product_template_attribute_value_ids', 'in', pt_attr_value_color.id),
                ('product_template_attribute_value_ids', 'in', pt_attr_value_talla.id)
            ])
            if product:
                product.write({'barcode':row[0], 'default_code':row[0]})

        if template_list:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'view_mode': 'list',
                'view_type': 'list',
                'views': [[False, 'list'], [False, 'form']],
                'domain': [('id', 'in', template_list)],
            }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mara.product.import',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
