from ome.omeMenus import export_menu_attributes

if __name__ == '__main__':
    try:
        output_path = export_menu_attributes('com.apple.mail')
        print(f'Menu attributes exported to: {output_path}')
    except Exception as e:
        print(f'Error exporting menu attributes: {e}') 