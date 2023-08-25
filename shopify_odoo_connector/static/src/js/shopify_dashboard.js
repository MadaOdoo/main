odoo.define('ShopifyDashboard.ShopifyDashboard', function(require) {
    'use strict';
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var web_client = require('web.web_client');
    var _t = core._t;
    var QWeb = core.qweb;
    var self = this;
    var ActionMenu = AbstractAction.extend({
        contentTemplate: 'ShopifyDashboard',
        events: {
            'click .customer': 'view_customer',
            'click .product': 'view_product',
            'click .order': 'view_order',
            'click #ttl_customers': 'view_customers',
            'click #ttl_products': 'view_products',
            'click #ttl_orders': 'view_orders',
        },
     start: function() {
     rpc.query({
            route: '/total_dashboard',
            params: {},
        }).then(function (result) {
          result.forEach(function(rec){
          document.getElementById("total_customers").innerHTML = rec['customer'];
          document.getElementById("total_products").innerHTML = rec['product'];
          document.getElementById("total_orders").innerHTML = rec['order'];
     })
     });
     rpc.query({
            route: '/dashboard',
            params: {},
        }).then(function (result) {
          console.log(result)
          result.forEach(function(rec){
              console.log(rec)
              google.charts.load('current', {'packages':['corechart']});
              google.charts.setOnLoadCallback(drawChart);

              function drawChart() {
               var data = google.visualization.arrayToDataTable([
                ["", "", { role: "style" } ],
                ["Customers", rec['customer'], "#b87333"],
                ["Products", rec['product'], "silver"],
                ["Orders", rec['order'], "gold"]
              ]);

              var options = {
                title: rec['instance'],
                titleTextStyle: {
                    fontSize: 15,
                    bold: true
                }
              };

                $("#dashboard").append("<div class='col' style='border: 2px  black; background-color: white; border-radius: 15px; max-width: 410px; width: 410px; height: 370px; margin-left: 0px; margin-bottom: 50px;'><div id="+ rec['id']+" style='border: 0px solid black; border-radius: 15px; width: 380px; height: 300px; margin-top: 0px;'/><div class='buttons' style=' display: flex; justify-content: space-around;'><button class='customer' value="+ rec['id'] +" style='border: 1px #b87333; background-color: #b87333; color: solid black; border-radius: 10px; width: 100px; height: 50px;'>Customers ("+rec['customer']+")</button><button class='product' value="+ rec['id'] +" style='border: 1px silver; background-color: silver; color: solid black; border-radius: 10px; width: 100px; height: 50px;'>Products ("+rec['product']+")</button><button class='order' value="+ rec['id'] +" style='border: 1px gold; background-color: gold; color: solid black; border-radius: 10px; width: 100px; height: 50px;'>Orders ("+rec['order']+")</button></div></div>")
                var chart = new google.visualization.ColumnChart(document.getElementById(rec['id']));

                chart.draw(data, options);

              }
          })
     })
      },
      view_customer: function(e) {
                var target = $(e.target);
                var value = target.val();
                console.log(value)
                this.do_action({
                    name: "Customers",
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids.instance_id', '=', parseInt(value)]],
                    target: 'current',
                })
      },
      view_product: function(e) {
                var target = $(e.target);
                var value = target.val();
                console.log(value)
                this.do_action({
                    name: "Products",
                    type: 'ir.actions.act_window',
                    res_model: 'product.template',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids.instance_id', '=', parseInt(value)]],
                    target: 'current',
                })
      },
      view_order: function(e) {
                var target = $(e.target);
                var value = target.val();
                console.log(value)
                this.do_action({
                    name: "Orders",
                    type: 'ir.actions.act_window',
                    res_model: 'sale.order',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids.instance_id', '=', parseInt(value)]],
                    target: 'current',
                })
      },

      view_customers: function(e) {
                this.do_action({
                    name: "Total Customers",
                    type: 'ir.actions.act_window',
                    res_model: 'res.partner',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids', '!=', false]],
                    target: 'current',
                })
      },
      view_products: function(e) {
                this.do_action({
                    name: "Total Products",
                    type: 'ir.actions.act_window',
                    res_model: 'product.template',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids', '!=', false]],
                    target: 'current',
                })
      },
      view_orders: function(e) {
                this.do_action({
                    name: "Total Orders",
                    type: 'ir.actions.act_window',
                    res_model: 'sale.order',
                    view_mode: 'tree,form',
                    views: [[false, 'list'],[false, 'form']],
                    domain: [['shopify_sync_ids', '!=', false]],
                    target: 'current',
                })
      },

    });
    core.action_registry.add('shopify_dashboard', ActionMenu);
});