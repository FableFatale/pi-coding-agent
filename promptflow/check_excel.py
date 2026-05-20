import zipfile
import xml.etree.ElementTree as ET

filepath = r'D:\pi-coding-agent\promptflow\data\真实对话\301564-94-公众话术（新系统）-已完成外呼记录_2026-04-15_09-47-38.csv'

def read_xlsx(filepath):
    """读取xlsx文件"""
    with zipfile.ZipFile(filepath, 'r') as z:
        # 读取共享字符串
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            with z.open('xl/sharedStrings.xml') as f:
                content = f.read().decode('utf-8')
                # 简单解析
                import re
                # 提取所有<si>标签内容
                si_matches = re.findall(r'<si>(.*?)</si>', content, re.DOTALL)
                for si in si_matches:
                    # 提取<t>标签内容
                    t_matches = re.findall(r'<t[^>]*>([^<]*)</t>', si)
                    strings.append(''.join(t_matches))
        
        print(f"共享字符串数量: {len(strings)}")
        print(f"前20个字符串: {strings[:20]}")
        
        # 读取工作表
        with z.open('xl/worksheets/sheet1.xml') as f:
            content = f.read().decode('utf-8')
            
            # 解析行
            import re
            row_matches = re.findall(r'<row[^>]*r="(\d+)"[^>]*>(.*?)</row>', content, re.DOTALL)
            
            print(f"\n总行数: {len(row_matches)}")
            
            # 处理前5行
            for row_num, row_content in row_matches[:5]:
                # 提取单元格
                cell_matches = re.findall(r'<c r="([A-Z]+\d+)"([^>]*)>(.*?)</c>', row_content, re.DOTALL)
                
                cells = []
                for cell_ref, cell_attrs, cell_content in cell_matches:
                    # 提取值
                    v_match = re.search(r'<v>(\d+)</v>', cell_content)
                    t_match = re.search(r't="([^"]+)"', cell_attrs)
                    
                    if v_match:
                        idx = int(v_match.group(1))
                        val = strings[idx] if idx < len(strings) else f"[idx:{idx}]"
                    else:
                        val = ""
                    
                    cells.append(f"{cell_ref}:{val[:30]}")
                
                print(f"\n行{row_num}: {cells}")

read_xlsx(filepath)
