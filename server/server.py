#!/home/programadorjoao/.virtualenvs/founse/bin/python
# QUANDO TERMINAR HTML O ESTILO DA PÁGINA E ESSAS COISAS, VOU MELHORAR O CÓDIGO

from quart import Quart, render_template, redirect, url_for, request, session, flash, get_flashed_messages
from secrets import token_urlsafe
import json

app = Quart('server', template_folder='../public')
app.secret_key = token_urlsafe(16)

async def define_template_in_post(user_informations, url_args, return_final_value=True,**kwargs):

    ur = await read_document_and_verify_infos(user_informations, 
    **kwargs)
    if not return_final_value:
        if ur != 'error':
            oi = await mkrightdict(user_informations, organize, True)
            for i in ('cities', 'districts', 'streets', 'houses'):
                if not user_informations.get(i, ''):
                    url_args[i] = oi[i]
            return url_args
    return ur

async def mkrightdict(dto, ro=False, continue_dict=False):
    wet = exclude_empty(dto)
    if ro:
        organized = ro(list(wet.keys()))
        if continue_dict:
            return {i: wet[i] for i in organized}
        return organized
    return wet

async def read_document_and_verify_infos(user_informations,**kwgs):
    bd = await read_json_document(kwgs['master_archive_name'])
    rf = await mkrightdict(user_informations)
    soo_kwgs = {'main': rf, 'cause_error': kwgs['eth'],
    'keys': organize(list(rf.keys()))}
    return await solve_recursive_objects(bd, kwgs['future_data'], **soo_kwgs)

def exclude_empty(dct):
    for i in list(dct):
        if not dct[i]:
            del dct[i]
    return dct

async def get_form():
    pre_form = await request.form
    return dict(pre_form)

def organize(keys):
    return [i for g in ('cities', 'districts', 'streets', 'numbers') for i in keys if i == g]

async def read_json_document(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        data = await load(file)
    return data

async def load(filename):
    return json.load(filename)

async def redirect_to(url, **url_values):
    if url_values:
        return redirect(url_for(url, **url_values))
    return redirect(url_for(url))

def capitalize_thing(obj: str):
    return ' '.join(i[0].upper() + i[1:] for i in obj.split())

async def solve_recursive_objects(master, return_args: dict, **kwgs):
    """It get data with a recursive way with the args of this being other dictionary's arguments"""
    main = kwgs['main']
    cause_error = kwgs['cause_error']
    keys = kwgs['keys']
    before_key = ''
    for e, i in enumerate(keys):
        if e > 0:
            return_args[before_key] = main[before_key]
        try:
            obj_list = master[i]
            for s in obj_list:
                if s["Name"] == capitalize_thing(main[i]):
                    master = s
                    break
            if master != obj_list:
                return_args[i] = obj_list
                before_key = i
                continue
            raise KeyError
        except KeyError:
            if cause_error[e]:
                return 'error'
            break

    return return_args

# HERE THE APP START

@app.route('/', methods=['GET', 'POST'])
async def index():
    form = await get_form()
    url_args = await mkrightdict(form, organize, continue_dict=True)
    if request.method == 'POST':
        ur = await define_template_in_post(url_args, {}, **{'eth': (True, True, False, False), 'future_data': {}, 'master_archive_name': 'data/houses.json'})
        if ur != 'error':
            session['user_informations'] = ur
            await flash('Search Made')
            return await redirect_to('houses', **url_args)
        form['error_message'] = 'Por favor insira algo válido'

    return await render_template('index.html', **form)

@app.route('/houses', methods=['GET', 'POST'])
async def houses():
    user_search = dict(request.args)
    if not user_search:
        return await redirect_to('index')
    form = await get_form()
    url_args = await mkrightdict(form, organize, True)
    error_hapnd = ''
    if request.method == 'POST':
        ur = define_template_in_post(url_args, {}, **{'eth': (True, True, False, False), 'future_data': {}, 'master_archive_name': 'data/houses.json'})
        if ur != 'error':
            session['user_informations'] = ur
            flash('Search made')
            return await redirect_to('houses', **url_args)
        error_hapnd = ur

    elif request.method == 'GET':
        if not get_flashed_messages():
            value_to_answer = user_search
        else:
            value_to_answer = session['user_informations']
        ur = await define_template_in_post(value_to_answer, {}, **{'eth': (True, True, False, False), 'future_data': {}, 'master_archive_name': 'data/houses.json'})
        if ur == 'error':
            error_hapnd = ur
        if len(list(ur.keys())) < 4:
            copy_of_ur = ur.copy()
            order_of_possible_keys_htf = ['districts', 'streets', 'houses'] #htf means "hard to find"
            for i in ur.keys(): 
                if type(copy_of_ur[i]) == list:
                    more_specific_values = copy_of_ur.pop(i)
            organizer_len = len(list(copy_of_ur.keys())) - 1
            final_value = []
            useful_order = order_of_possible_keys_htf[organizer_len:]
            for i in useful_order:
                counter = 0
                next_ld = []
                for x in more_specific_values:
                    if i != 'houses':
                        dict_of_time = dict(copy_of_ur, 
                        **{i: x['Name']}
                        )
                        for j in x[useful_order[useful_order.index(i) + 1]]:
                            next_ld.append(j)
                    else:
                        dict_of_time = dict(copy_of_ur, 
                        **{i: x}
                        )

                    if useful_order.index(i) == 0:
                        final_value.append({})
                    try:
                        final_value[counter].update(dict_of_time)
                    except:
                        final_value.append(dict(final_value[counter-1], **dict_of_time))
                    counter += 1

                more_specific_values = next_ld
        if error_hapnd == 'error':
            form['error_message'] = 'Por Favor insira algo válido'
            return await render_template('houses.html', **form)
        return await render_template('houses.html', **dict(form, **{'informations_returned': final_value}))
                                                        
            
if __name__ == '__main__':
    app.run(debug=True)