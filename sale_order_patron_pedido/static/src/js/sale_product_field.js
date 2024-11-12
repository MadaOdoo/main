/** @odoo-module **/

import Dialog from 'web.Dialog';
import { qweb } from "web.core";
import { patch } from "@web/core/utils/patch";
import { SaleOrderLineProductField } from '@sale/js/sale_product_field';
import { formatMonetary } from "@web/views/fields/formatters";
const { markup } = owl;

patch(SaleOrderLineProductField.prototype, 'sale_order_patron_pedido', {

    _imageUrl: function(id) {
        return `/web/image?model=product.template&field=image_256&id=${id}`;
    },

    /**
     * Triggers Matrix Dialog opening
     *
     * @param {String} jsonInfo matrix dialog content
     * @param {integer} productTemplateId product.template id
     * @param {editedCellAttributes} list of product.template.attribute.value ids
     *  used to focus on the matrix cell representing the edited line.
     *
     * @private
    */
     _openMatrixConfigurator: function (jsonInfo, productTemplateId, editedCellAttributes) {
        const infos = JSON.parse(jsonInfo);
        const record_patron = infos.record_patron
        const has_record_patron = infos.has_record_patron
        const saleOrderRecord = this.props.record.model.root;
        const img_product = this._imageUrl(productTemplateId)

        const MatrixDialog = new Dialog(this, {
            title: this.env._t('Choose Product Variants'),
            size: 'extra-large', // adapt size depending on matrix size?
            $content: $(qweb.render(
                'product_matrix.matrix', {
                    header: infos.header,
                    rows: infos.matrix,
                    product_img: img_product,
                    record_patron: record_patron,
                    has_record_patron: has_record_patron,
                    // agregando nuevo campo de pares totales
                    //totalPares: calculateTotalPares(),
                    format({price, currency_id}) {
                        if (!price) { return ""; }
                        const sign = price < 0 ? '-' : '+';
                        const formatted = formatMonetary(
                            Math.abs(price),
                            {
                                currencyId: currency_id,
                            },
                        );
                        return markup(`${sign}&nbsp;${formatted}`);
                    }
                }
            )),
            buttons: [
                {text: this.env._t('Confirm'), classes: 'btn-primary', close: true, click: function (result) {
                    const $inputs = this.$('.o_matrix_input');
                    var matrixChanges = [];
                    _.each($inputs, function (matrixInput) {
                        if (matrixInput.value && matrixInput.value !== matrixInput.attributes.value.nodeValue) {
                            matrixChanges.push({
                                qty: parseFloat(matrixInput.value),
                                ptav_ids: matrixInput.attributes.ptav_ids.nodeValue.split(",").map(function (id) {
                                      return parseInt(id);
                                }),
                            });
                        }
                    });
                    if (matrixChanges.length > 0) {
                        // NB: server also removes current line opening the matrix
                        saleOrderRecord.update({
                            grid: JSON.stringify({changes: matrixChanges, product_template_id: productTemplateId}),
                            grid_update: true // to say that the changes to grid have to be applied to the SO.
                        });
                    }
                }},
                {text: this.env._t('Close'), close: true},
            ],
        }).open();

        // Funcion de calculo de total de pares:
        const calculateTotalPares = () => {
            let totalPares = 0;
            const $inputs = MatrixDialog.$content.find('.o_matrix_input');
            $inputs.each(function () {
                const value = parseFloat(this.value) || 0;
                totalPares += value;
            });
            return totalPares;
        };

        MatrixDialog.opened(function () {
            MatrixDialog.$content.closest('.o_dialog_container').removeClass('d-none');
            if (editedCellAttributes.length > 0) {
                const str = editedCellAttributes.toString();
                MatrixDialog.$content.find('.o_matrix_input').filter((k, v) => v.attributes.ptav_ids.nodeValue === str)[0].focus();
            } else {
                MatrixDialog.$content.find('.o_matrix_input:first()').focus();
            }

            function changeValues(currentValue){
                const $inputs = MatrixDialog.$content.find('.o_matrix_input');
                _.each($inputs, function (matrixInput){
                    const ptav_ids = matrixInput.attributes.ptav_ids
                    let objetoConId1 = record_patron.find(obj => obj.id == currentValue);
                    let searchObjt = objetoConId1.tallas[parseInt(ptav_ids.nodeValue)]
                    if (searchObjt !== undefined && searchObjt > 0){
                        matrixInput.value = searchObjt
                        matrixInput.attributes.value.nodeValue = 0
                    }
                    else{
                        matrixInput.value = 0
                        matrixInput.attributes.value.nodeValue = 0
                    }
                })
            }

            const value_current = MatrixDialog.$content.find('.js_select_patron').val()
            if ((value_current !== undefined || value_current > 0) && editedCellAttributes.length === 0){
                changeValues(value_current)
            }


            // Evento para recalcular el total de pares cuando se cambie un valor en la matriz
            MatrixDialog.$content.find('.o_matrix_input').on('change', function () {
                const totalPares = calculateTotalPares();
                MatrixDialog.$content.find('.js_total_pares').text(totalPares);
            });

            ////////////////////////////////////
            // Evento para recalcular el total de pares cuando cambie el select_patron
            MatrixDialog.$content.find('.js_select_patron').on('change', function () {
                // Actualiza los valores en la matriz según el patrón seleccionado
                const selectedValue = this.value;
                changeValues(selectedValue);

                // Recalcula el total de pares después de cambiar el patrón
                const totalPares = calculateTotalPares();
                MatrixDialog.$content.find('.js_total_pares').text(totalPares);
            });

            ///////////////////////////////////
            MatrixDialog.$content.find('.js_select_patron').on('change', (event) => {
                event.preventDefault();
                const selectedValue = event.target.value;
                changeValues(selectedValue)
            });

            // Recalcula y establece el total de pares una vez que el diálogo está completamente cargado
            const initialTotalPares = calculateTotalPares();
            MatrixDialog.$content.find('.js_total_pares').text(initialTotalPares);

        });
    },
});