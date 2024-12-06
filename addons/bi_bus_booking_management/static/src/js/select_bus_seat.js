document.addEventListener("click", (event) => {
    if (event.target && event.target.id === "show_bus_seat") {
        var settings = {
            rows: document.querySelector('#total_row').value,
            cols: document.querySelector('#total_seat_in_single_row').value,
            rowCssPrefix: 'row-',
            colCssPrefix: 'col-',
            seatWidth: 35,
            seatHeight: 35,
            seatCss: 'seat',
            selectedSeatCss: 'selectedSeat',
            selectingSeatCss: 'selectingSeat'
        };
        document.querySelector('#show_bus_seat').disabled = true;
        document.querySelector('#bus_seat_view_div').style.width = "300px";
        document.querySelector('#bus_seat_view_div').style.height = "300px";

        let booked_seat = [];
        if (document.querySelector('#booked_seat').value) {
            booked_seat = JSON.parse(document.querySelector('#booked_seat').value);
        }

        let str = [], seatNo, className;
        if (document.querySelector("#bus_type").value === "seating") {
            for (let i = 0; i < document.querySelector('#total_row').value; i++) {
                for (let j = 0; j < document.querySelector('#total_seat_in_single_row').value; j++) {
                    seatNo = (i + j * document.querySelector('#total_row').value + 1);
                    className = `${settings.seatCss} ${settings.rowCssPrefix}${i} ${settings.colCssPrefix}${j}`;

                    if (Array.isArray(booked_seat) && booked_seat.includes(seatNo)) {
                        className += ` ${settings.selectedSeatCss}`;
                    }

                    str.push(
                        `<li class="${className}" data-id="${seatNo}" 
                          style="top:${i * settings.seatHeight}px;left:${j * settings.seatWidth * 2}px">
                          <a title="${seatNo}">${seatNo}</a>
                        </li>`
                    );
                }
            }
            document.querySelector('#bus_seat_view_ul').innerHTML = str.join('');
        } else if (document.querySelector("#bus_type").value === "sleeper") {
            for (let i = 0; i < document.querySelector('#total_row').value; i++) {
                for (let j = 0; j < document.querySelector('#total_seat_in_single_row').value; j++) {
                    seatNo = (i + j * document.querySelector('#total_row').value + 1);
                    className = `${settings.seatCss} ${settings.rowCssPrefix}${i} ${settings.colCssPrefix}${j}`;

                    if (Array.isArray(booked_seat) && booked_seat.includes(seatNo)) {
                        className += ` ${settings.selectedSeatCss}`;
                    }

                    str.push(
                        `<li class="${className}" data-id="${seatNo}" 
                          style="top:${i * settings.seatHeight}px;left:${j * settings.seatWidth * 2}px" 
                          title="${seatNo}">
                        </li>`
                    );
                }
            }
            document.querySelector('#bus_seat_view_sleeper_ul').innerHTML = str.join('');
        }
    }

    if(document.querySelector('#total_row') && document.querySelector('#total_seat_in_single_row')){
        var settings = {
            rows: document.querySelector('#total_row').value,
            cols: document.querySelector('#total_seat_in_single_row').value,
            rowCssPrefix: 'row-',
            colCssPrefix: 'col-',
            seatWidth: 35,
            seatHeight: 35,
            seatCss: 'seat',
            selectedSeatCss: 'selectedSeat',
            selectingSeatCss: 'selectingSeat'
        };

        if (event.target.classList.contains(settings.seatCss)) {
            if (event.target.classList.contains(settings.selectedSeatCss)) {
                alert('This seat is already booked');
            } else {
                event.target.classList.toggle(settings.selectingSeatCss);
                if (event.target.classList.contains(settings.selectingSeatCss)) {
                    document.querySelector("#bus_customer_table").style.display = "block";
                    document.querySelector("#button_checkout").style.display = "block";
                    document.querySelector(".o_bus_list_body").insertAdjacentHTML("beforeend", `
                        <tr id="tr_p${event.target.dataset.id}">
                            <td><input type="textbox" name="seat_number${event.target.dataset.id}" readonly
                                id="seat_number_${event.target.dataset.id}" value="${event.target.dataset.id}" style="width: 10em;height:2em;" required /></td>
                            <td><input style="width: 10em;height:2em;" type="textbox" name="name${event.target.dataset.id}" id="name_${event.target.dataset.id}" required /></td>
                            <td><input style="width: 10em;height:2em;" type="textbox" name="email${event.target.dataset.id}" data-id="email_${event.target.dataset.id}" required /></td>
                            <td><input type="number" name="age${event.target.dataset.id}" data-id="age_${event.target.dataset.id}" min="1" required style="width: 10em;height:2em;" /></td>
                            <td><select style="width: 10em;height:2em;" name="gender${event.target.dataset.id}" data-id="gender_${event.target.dataset.id}" required>
                                <option value="">-Select Gender-</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select></td>
                            <td><input style="width: 10em;height:2em;" type="textbox" name="number${event.target.dataset.id}" data-id="number_${event.target.dataset.id}" required /></td>
                            <td><input type="hidden" name="seat_line${event.target.dataset.id}" readonly id="seat_line_${event.target.dataset.id}" value="${event.target.dataset.id}" /></td>
                        </tr>
                    `);
                } else {
                    document.querySelector(`#tr_p${event.target.dataset.id}`).remove();
                    if (!document.querySelector(".o_bus_list_body tr")) {
                        document.querySelector("#bus_customer_table").style.display = "none";
                        document.querySelector("#button_checkout").style.display = "none";
                    }
                }
            }
        }
    }
});