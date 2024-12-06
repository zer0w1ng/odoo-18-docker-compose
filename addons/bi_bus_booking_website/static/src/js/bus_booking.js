/** @odoo-module **/


    // import { jsonrpc } from "@web/core/network/rpc_service";
    import { rpc } from "@web/core/network/rpc";

    $(document).ready(function(){
        $("#button_bus_search").click(function () {
            var datetime = new Date().toJSON().slice(0, 10);
            if ($('#start_point').val().length === 0){
                window.alert("Please add start point.")
            }
            else if ($('#end_point').val().length === 0){
                window.alert("Please add end point.")
            }
            else if ($('#bus_journey_date_id').val().length === 0){
                window.alert("Please add date!!")
            }
            else if ($('#bus_types').val().length === 0){
                window.alert("Please add bus types.")
            }
            else if ($('#start_point').val() === $('#end_point').val()){
                window.alert("Start and end point should be different.")
            }
            else if($('#bus_journey_date_id').val() < datetime){
                window.alert("You can not select the past date.")
            }
            if ($('#start_point').val().length && $('#end_point').val().length
                && $('#bus_journey_date_id').val().length && $('#bus_types').val().length
                && $('#bus_journey_date_id').val() >= datetime
                && $('#start_point').val() != $('#end_point').val()){
               rpc('/search_bus', {
                                    start_point: $('#start_point').val(),
                                    end_point: $('#end_point').val(),
                                    bus_journey_date_id: $('#bus_journey_date_id').val(),
                                    bus_types: $('#bus_types').val(),
                }).then(function (res){
                                       if (res){
                                                $("#bus_list_table").show()
                                                var counter = 1;
                                                for(var i = 0; i < res.length; i++){
                                                    $(".o_bus_list_body").append("<tr>\
                                                                                <td>" + res[i]['route'] +"</td>\
                                                                                <td>" + res[i]['m2o_fleet_vehicle_id'] +"</td>\
                                                                                <td>" + res[i]['m2o_bus_point_pickup_id'] +"</td>\
                                                                                <td>" + res[i]['m2o_bus_point_dropoff_id'] +"</td>\
                                                                                <td>" + res[i]['m2o_bus_types_id'] +"</td>\
                                                                                <td>" + res[i]['date'] +"</td>\
                                                                                <td>" + res[i]['total_seats'] +"</td>\
                                                                                <td>" + res[i]['remaining_seat'] +"</td>\
                                                                                <td>" + res[i]['start_time'] +"</td>\
                                                                                <td>" + res[i]['end_time'] +"</td>\
                                                                                <td><a type='button' class='btn btn-primary btn-lg oe_button_bus_book' \
                                                                          id='"+ res[i]['routes_line']+"' href='/bus_booking_confirm/"+ res[i]['routes_line']+"'>Book</a></td></tr>"
                                                    )
                                                }
                                                $('#button_bus_search').prop('disabled', true) 

                                       }
                                       else{
                                            $("#bus_list_table").hide()
                                            alert("Buses not available.");
                                        }
                });
            }
        });
        var settings = {
               rows: $("#total_row").val(),
               cols: $("#total_seat_in_single_row").val(),
               rowCssPrefix: 'row-',
               colCssPrefix: 'col-',
               seatWidth: 50,
               seatHeight: 50,
               seatCss: 'seat',
               selectedSeatCss: 'selectedSeat',
               selectingSeatCss: 'selectingSeat'
        };
        $(document).on('click', '#show_bus_seat', function(event){
            $('#show_bus_seat').prop('disabled', true) 
            $('#bus_seat_view_div').css("width", 550); 
            $('#bus_seat_view_div').css("height", 300); 

            if ($("#booked_seat").val()){
                var booked_seat = JSON.parse($("#booked_seat").val());
            }
            if ($("#bus_type").val() == "seating"){
            var str = [], seatNo, className;
            for (var i = 0; i < $("#total_row").val(); i++) {
                for (var j = 0; j < $("#total_seat_in_single_row").val(); j++) {
                    seatNo = (i + j * $("#total_row").val() + 1);
                    className = settings.seatCss + ' ' + settings.rowCssPrefix + i.toString() + ' ' + settings.colCssPrefix + j.toString();
                    if ($.isArray(booked_seat) && $.inArray(seatNo, booked_seat) != -1) {
                            className += ' ' + settings.selectedSeatCss;
                    }
                    str.push('<li class="' + className + '"' + 'data-id="'+ seatNo +'"'+
                                'style="top:' + (i * settings.seatHeight).toString() + 'px;left:' + (j * settings.seatWidth * 2).toString() + 'px">' +
                                '<a title="' + seatNo + '">' + seatNo + '</a>' +
                                '</li>');
                }
            }
            $('#bus_seat_view_ul').html(str.join(''));
            }
            else if ($("#bus_type").val() == "sleeper"){
            var str = [], seatNo, className;
            for (var i = 0; i < $("#total_row").val(); i++) {
                for (var j = 0; j < $("#total_seat_in_single_row").val(); j++) {
                    seatNo = (i + j * $("#total_row").val() + 1);
                    className = settings.seatCss + ' ' + settings.rowCssPrefix + i.toString() + ' ' + settings.colCssPrefix + j.toString();
                    if ($.isArray(booked_seat) && $.inArray(seatNo, booked_seat) != -1) {
                            className += ' ' + settings.selectedSeatCss;
                    }
                    str.push('<li class="' + className + '"' + 'data-id="'+ seatNo +'"'+
                                'style="top:' + (i * settings.seatHeight).toString() + 'px;left:' + (j * settings.seatWidth * 2).toString() + 'px" title="'+ seatNo +'">' +
                                '</li>');
                }
            }
            $('#bus_seat_view_sleeper_ul').html(str.join(''));
            }
        });

        $(document).on('click', '.' + settings.seatCss, function(event){
            if ($(this).hasClass(settings.selectedSeatCss)){
                alert('This seat is already booked');
            }
            else{
                $(this).toggleClass(settings.selectingSeatCss);
                if ($(this).hasClass(settings.selectingSeatCss)){
                    $("#bus_customer_table").show()
                    $("#button_checkout").show()
                    $(".o_bus_list_body").append("<tr id='tr_p"+event["target"]["dataset"]["id"]+"'>\
                                        <td><input style='width:100%' type='textbox' name='seat_number"+event["target"]["dataset"]["id"]+"' readonly='1'\
                                            id='seat_number_"+event["target"]["dataset"]["id"]+"' value='"+event["target"]["dataset"]["id"]+"' width='10%' required='1'/></td>\
                                        <td><input style='width:100%' type='textbox' name='name"+event["target"]["dataset"]["id"]+"' id='name_"+event["target"]["dataset"]["id"]+"' required='1'/></td>\
                                        <td><input style='width:100%' type='textbox' name='email"+event["target"]["dataset"]["id"]+"' data-id='email_"+event["target"]["dataset"]["id"]+"' \
                                            required='1'/></td>\
                                        <td><input style='width:100%' type='number' name='age"+event["target"]["dataset"]["id"]+"' \
                                            data-id='age_"+event["target"]["dataset"]["id"]+"' \
                                            min='1' required='1'/></td>\
                                        <td><select style='width: 10em;height:2em;' name='gender"+event["target"]["dataset"]["id"]+"' data-id='gender_"+event["target"]["dataset"]["id"]+"' \
                                               required='1'>\
                                            <option value=''>-Select Gender-</option>\
                                            <option value='Male'>Male</option>\
                                            <option value='Female'>Female</option>\
                                            <option value='Other'>Other</option>\
                                            </select>\
                                        </td>\
                                        <td><input style='width:100%' type='textbox' name='number"+event["target"]["dataset"]["id"]+"' data-id='number_"+event["target"]["dataset"]["id"]+"' \
                                            required='1'/></td>\
                                        <td><input type='hidden' name='seat_line"+event["target"]["dataset"]["id"]+"' readonly='1'\
                                            id='seat_line_"+event["target"]["dataset"]["id"]+"' value='"+event["target"]["dataset"]["id"]+"'/></td>\
                                        </tr>"
                    )
                }
                else{
                    var tr_p = "#tr_p"+event["target"]["dataset"]["id"]
                    $(tr_p).remove();
                    if(!$(".o_bus_list_body tr").length){
                        $("#bus_customer_table").hide()
                        $("#button_checkout").hide()
                    }
                }

            }
        })

        $("#button_bus_clear_search").click(function () {
            $(".o_bus_list_body tr").remove();
            $('#button_bus_search').prop('disabled', false) 

        })

    });