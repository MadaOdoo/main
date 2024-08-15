Technical name: l10n_mx_pos_global_invoice

Version: 16.0.0.0

Category: Invoice

Author: Xmarts Group

Website: www.xmarts.com

Depends:

. Point of Sale (point_of_sale)

. Inventory (stock)

. Invoicing (account)

Sumary:

Este módulo permite la creación de factura global de una sesión en un PDV . La factura global se crea con todos las ordenes de ventas no facturadas a un cliente en especifico ejemplo Público General description:

Para la configuración de pos global invoice debes realizar los siguientes pasos

Paso uno : Abrimos la app de punto de venta como hace referencia la imagen 1.1

Paso dos : Dentro de la app podemos visualizar las tiendas o bodegas y nos encontramos del lado derecho tres puntitos que nos da un mini menú de opciones que son ver,órdenes,sesiones,reporte,editar. elegimos editar y nos llevara para otro menú

Paso tres : Aquí podemos ver las siguientes opciones crear la factura global,múltiple empleado por sesión,caja lot,impresora de epos. activamos el check crear factura global

Paso cuatro : Una vez activado el check veremos las siguientes preguntas. . General public (Cliente al que va dirigida la factura)

    . Method (Manual o Automático)

    . Manual (Creas manualmente la factura global)

    . Automático (Al cerrar sesion se crea en automático la factura)

    . Diario (Al que va dirigida la factura)

    . Periodicidad (Apartado de periodicidad en el xml que desean que lleva al timbrar la factura). ya configurado guardamos.

Paso cinco : Abrimos el apartado se sesiones elegimos una para que nos de el boton de accion es prioridad estar en vista lista

Release notes 16.0.0 Soporte para la creación de factura global

License Odoo Enterprise Edition License v1.0 https://www.odoo.com/documentation/16.0/es/legal/licenses.html#odoo-16-enterprise-edition
