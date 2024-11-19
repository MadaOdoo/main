odoo.define('xma_pos_voucher_redemption.pos', function (require) {
    "use strict";

    var { PosGlobalState, Payment, Order } = require('point_of_sale.models');
    const Registries = require('point_of_sale.Registries');


    const XmaPosVoucherRedemtionPosGlobalState = (PosGlobalState) => class XmaPosVoucherRedemtionPosGlobalState extends PosGlobalState {
        async _processData(loadedData) {
            await super._processData(...arguments);
            this.journal_by_id = loadedData['journal_by_id'];
        }
    }
    Registries.Model.extend(PosGlobalState, XmaPosVoucherRedemtionPosGlobalState);

    const XmaPosVoucherRedemtionPayment = (Payment) => class XmaPosVoucherRedemtionPayment extends Payment {
        // @Override
        constructor() {
            super(...arguments);
            this.folio_de_vale = this.folio_de_vale || null;
        }
        //@Override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.folio_de_vale = json.folio_de_vale;
        }
        export_as_JSON() {
            var json = super.export_as_JSON(...arguments);

            var to_return = _.extend(json, {
                'folio_de_vale': this.folio_de_vale,
            });
            return to_return;
        }
    }
    Registries.Model.extend(Payment, XmaPosVoucherRedemtionPayment);

    const XmaPosVoucherRedemtionOrder = (Order) => class XmaPosVoucherRedemtionOrder extends Order {
        // @Override
        constructor() {
            super(...arguments);
            this.is_vale = this.is_vale || null;
            this.folio_de_vale = this.folio_de_vale || null;
            this.state_de_vale = this.state_de_vale || null;
            this.distribuidora_id = this.distribuidora_id || null;
            this.nombre_distribuidora = this.nombre_distribuidora || null;
            this.cantidad_pagos = this.cantidad_pagos || null;
            this.monto_seguro = this.monto_seguro || null;
            this.pago_quincenal = this.pago_quincenal || null;
            this.total = this.total || null;
            this.fecha = this.fecha || null;
            this.config_id = this.config_id || null;
            this.nombre_cliente = this.nombre_cliente || null;
            this.cliente_telefono = this.cliente_telefono || null;
            this.ife = this.ife || null;
            this.monto_total = this.monto_total || null;
            this.monto_as_text = this.monto_as_text || null;
            this.ciudad = this.ciudad || null;
            this.str_fechas = this.str_fechas || null;
            this.porcentaje_comision = this.porcentaje_comision || null;
            this.monto_seguro_por_quincena = this.monto_seguro_por_quincena || null;
        }
        //@Override
        init_from_JSON(json) {
            super.init_from_JSON(...arguments);
            this.is_vale = json.is_vale;
            this.folio_de_vale = json.folio_de_vale;
            this.state_de_vale = json.state_de_vale;
            this.distribuidora_id = json.distribuidora_id;
            this.nombre_distribuidora = json.nombre_distribuidora;
            this.cantidad_pagos = json.cantidad_pagos;
            this.monto_seguro = json.monto_seguro;
            this.pago_quincenal = json.pago_quincenal;
            this.total = json.total;
            this.fecha = json.fecha;
            this.config_id = json.config_id;
            this.nombre_cliente = json.nombre_cliente;
            this.cliente_telefono = json.cliente_telefono;
            this.ife = json.ife;
            this.monto_total = json.monto_total;
            this.monto_as_text = json.monto_as_text;
            this.ciudad = json.ciudad;
            this.str_fechas = json.str_fechas;
            this.porcentaje_comision = json.porcentaje_comision;
            this.monto_seguro_por_quincena = json.monto_seguro_por_quincena;
        }
        export_as_JSON() {
            var json = super.export_as_JSON(...arguments);

            var to_return = _.extend(json, {
                'is_vale': this.is_vale,
                'folio_de_vale': this.folio_de_vale,
                'state_de_vale': this.state_de_vale,
                'distribuidora_id': this.distribuidora_id,
                'nombre_distribuidora': this.nombre_distribuidora,
                'cantidad_pagos': this.cantidad_pagos,
                'monto_seguro': this.monto_seguro,
                'pago_quincenal': this.pago_quincenal,
                'total': this.total,
                'fecha': this.fecha,
                'config_id': this.config_id,
                'nombre_cliente': this.nombre_cliente,
                'cliente_telefono': this.cliente_telefono,
                'ife': this.ife,
                'monto_total': this.monto_total,
                'monto_as_text': this.monto_as_text,
                'ciudad': this.ciudad,
                'str_fechas': this.str_fechas,
                'cliente_telefono': this.cliente_telefono,
                'porcentaje_comision': this.porcentaje_comision,
                'monto_seguro_por_quincena': this.monto_seguro_por_quincena
            });
            return to_return;
        }
        export_for_printing(){
            var json = super.export_for_printing(...arguments);

            var to_return = _.extend(json, {
                is_vale: this.is_vale,
                cantidad_pagos: this.cantidad_pagos,
                pago_quincenal: this.pago_quincenal,
                monto_seguro: this.monto_seguro,
                total: this.total,
                // nombre_cliente: this.nombre_cliente,
                // cliente_telefono: this.cliente_telefono,
                // ife: this.ife,
                folio_de_vale: this.folio_de_vale,
                nombre_distribuidora: this.nombre_distribuidora,
                fecha: this.fecha,
                monto_total: this.monto_total,
                monto_as_text: this.monto_as_text,
                ciudad: this.ciudad,
                // Get today's date as DD MM YYYY with MM as a three letter string with no libraries
                today: new Date().toLocaleDateString('es-MX', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric'
                }),
                uid: this.uid
            });
            return to_return;
        }
    }
    Registries.Model.extend(Order, XmaPosVoucherRedemtionOrder);
});