from flask import Flask, render_template, request, redirect, flash, send_from_directory
from datetime import datetime
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST':
        name = request.form.get('name') if request.form.get('name') else ""
        address = request.form.get('address') if request.form.get('address') else ""
        load_kw = float(request.form.get('loadKW'))
        load_hp = float(request.form.get('loadHP'))
        previous_units = float(request.form.get('previousConsumption'))
        current_units = float(request.form.get('currentConsumption'))
        units = int(current_units - previous_units)
        billing_type = request.form.get('billingOptionsRadios')
        start_date = datetime.strptime(request.form.get('startdate'), '%Y-%m-%d').strftime('%d/%m/%Y')
        end_date = datetime.strptime(request.form.get('enddate'), '%Y-%m-%d').strftime('%d/%m/%Y')
        contracted_load = (0.746 * load_hp) + load_kw

        contracted_load = round(contracted_load * 2) / 2 # rounding to nearest 0.5

        cca = 0
        ccb = 0
        if billing_type == "Commercial":
            if 0 < contracted_load > 1:
                cca = contracted_load * 80
        else:
            if 0 < contracted_load > 1:
                cca = 1 * 60
                ccb = (contracted_load - 1) * 70
            else:
                cca = contracted_load * 60

        slab_rates = set_slab_rates(billing_type)
        slabs = calculate_slabs(units, slab_rates, billing_type)
        tax = round(((slabs[0][0] + slabs[1][0] + slabs[2][0] + slabs[3][0] ) * 9)/100, 2)
        fuel_cess = round(units * 0.29, 2)        
        discount = round(tax + fuel_cess, 2)
        total = round(cca+ccb+slabs[0][0] + slabs[1][0] + slabs[2][0] + slabs[3][0] + discount, 2)
        net_bill = round(cca+ccb+slabs[0][0] + slabs[1][0] + slabs[2][0] + slabs[3][0] , 2)

        return render_template('submitted.html', name=name, address=address, previousConsumption=previous_units, 
                                currentConsumption = current_units, load_kw=load_kw, load_hp=load_hp, 
                                units=units, discount = format(discount, '.2f'), billing_type=billing_type, 
                                cca=format(cca, '.2f'), ccb=format(ccb, '.2f'), 
                                slab1=format(slabs[0][0], '.2f'), slab1_units=slabs[0][1],
                                slab2=format(slabs[1][0], '.2f'), slab2_units=slabs[1][1],
                                slab3=format(slabs[2][0], '.2f'), slab3_units=slabs[2][1],
                                slab4=format(slabs[3][0], '.2f'), slab4_units=slabs[3][1],
                                fuelcess=format(fuel_cess, '.2f'), tax=format(tax, '.2f'), 
                                netbill=format(net_bill, '.2f'), contracted_load=round(contracted_load,1), 
                                total = format(total, '.2f'),
                                slab1rate=format(slab_rates[0], '.2f'), slab2rate=format(slab_rates[1], '.2f'),
                                slab3rate=format(slab_rates[2], '.2f'), slab4rate=format(slab_rates[3], '.2f'), 
                                startdate = start_date, enddate = end_date )
    else:
        return render_template('home.html')

def set_slab_rates(billing_type):
    if billing_type=="Urban":
        slab1_rate = 3.75
        slab2_rate = 5.20
        slab3_rate = 6.75
        slab4_rate = 7.80
    elif billing_type == "Rural":
        slab1_rate = 3.65
        slab2_rate = 4.90
        slab3_rate = 6.45
        slab4_rate = 7.30
    elif billing_type=="Commercial":
        slab1_rate = 8.00
        slab2_rate = 9.00
        slab3_rate = 0
        slab4_rate = 0
    return([slab1_rate, slab2_rate, slab3_rate, slab4_rate])


def calculate_slabs(units, slab_rates, billing_type):
    if billing_type == "Urban" or billing_type == "Rural":
        slab1 = 0
        slab1_units = 0
        slab2 = 0
        slab2_units = 0
        slab3 = 0
        slab3_units = 0
        slab4 = 0
        slab4_units = 0
        if units > 30:
            slab1 = 30 * slab_rates[0]
            slab1_units = 30
            units = units - 30
            if units > 70:
                slab2 = 70 * slab_rates[1]
                slab2_units = 70
                units = units - 70
                if units > 100:
                    slab3 = 100 * slab_rates[2]
                    slab3_units = 100
                    units = units - 100
                    if units > 0:
                        slab4 = 100 * slab_rates[3]
                        slab4_units = units
                else:
                    slab3_units = units
                    slab3 = units * slab_rates[2]
            else:
                slab2_units = units
                slab2 = units * slab_rates[1]
        else:
            slab1_units = units
            slab1 = units * slab_rates[0]
        return([[round(slab1, 2), slab1_units], [round(slab2, 2), slab2_units], [round(slab3, 2), slab3_units], 
                [round(slab4, 2), slab4_units]])
    else:
        slab1 = 0
        slab2 = 0
        if units > 50:
            slab1 = 50 * slab_rates[0]
            slab1_units = 50
            units = units - 50
            if units > 0:
                slab2_units = units
                slab2 = units * slab_rates[1]
        else:
            slab2_units = units
            slab1 = units * slab_rates[0]
        return([[round(slab1, 2), slab1_units], [round(slab2, 2), slab2_units], [0, 0], [0, 0]])

if __name__ == '__main__':
    app.run(debug=True)
