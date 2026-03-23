from pprint import pprint
import xmlrpc.client

def create_db(url, master_password, new_db_name, admin_password, demo_data=False, lang="en_US"):
    db_manager = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")

    try:
        print(f"Creating database {new_db_name}...")
        db_manager.create_database(master_password, new_db_name, demo_data, lang, admin_password)
        print("Success!")
    except Exception as e:
        print(f"Error: {e}")


def delete_db(url, master_password, db_to_delete):
    db_manager = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/db")
    try:
        # This removes the Postgres DB and the Odoo filestore
        success = db_manager.drop(master_password, db_to_delete)
        if success:
            print(f"Database '{db_to_delete}' deleted successfully.")
        else:
            print("Failed to delete database. Check permissions.")
    except Exception as e:
        print(f"Error: {e}")


def install_modules(url, db, modules_to_install, username="admin", password="12345"):
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    # print(db, username, password, uid)

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    # module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', 
    #     [[['name', 'in', modules_to_install]]])

    # if module_ids:
    #     print(f"Installing modules: {modules_to_install}...")
    #     models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [module_ids])
    #     print("Installation triggered successfully.")
    for module_name in modules_to_install:
        maintain_module(db, uid, password, models, module_name)


def uninstall_modules(url, db, modules_to_uninstall, username="admin", password="12345"):
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    for module in modules_to_uninstall:
        print(f"Uninstalling modules: {module}...")
        module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', 
            [[['name','=',module]]])
        for module_id in module_ids:
            try:
                models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_uninstall', [[module_id]])
                print("Uninstallation triggered successfully.")
            except Exception as e:
                print(f"Error {module}:\n{e}")
        


def maintain_module(db, uid, password, models, module_name):
    # 1. Search for the module by technical name
    module_data = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', 
        [[['name', '=', module_name]]], 
        {'fields': ['id', 'state']})

    if not module_data:
        print(f"Module '{module_name}' not found in the addons path.")
        return

    module = module_data[0]
    module_id = module['id']
    current_state = module['state']

    # 2. Decide Action
    if current_state == 'installed':
        print(f"Module '{module_name}' is already installed. Upgrading...")
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [[module_id]])
        print("Upgrade complete.")
    else:
        print(f"Module '{module_name}' is {current_state}. Installing...")
        models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_install', [[module_id]])
        print("Installation complete.")


if __name__=="__main__":
    # url = "http://localhost:10018"
    url = "http://localhost:10019"
    master_password = "minhng.info"
    #master_password = "ebfeYUx2i5D2PZ6"
    new_db_name = "demo-pay"
    admin_password = "12345"
    demo = True

    if 0:
        #create new db
        delete_db(url, master_password, new_db_name)
        create_db(url, master_password, new_db_name, admin_password, demo_data=demo)
        install_modules(url, new_db_name, ['contacts','muk_web_theme'])

    if 1:
        #testing
        modules = ['ez_hr']
        modules_to_uninstall = modules
        modules_to_install = modules

        uninstall_modules(url, new_db_name, modules_to_uninstall)
        install_modules(url, new_db_name, modules_to_install)

    if 0:
        #fresh install
        modules_to_uninstall = ['ez_hr_namesplit','ez_hr','hr']
        uninstall_modules(url, new_db_name, modules_to_uninstall)

        modules_to_install = ['ez_hr_namesplit']
        install_modules(url, new_db_name, modules_to_install)
