import re

def refactor():
    with open('views/dashboard.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Part 1: Remove left, right columns and unindent the table
    # Replace the wrapper
    pattern1 = r"    # ── Konten utama: Prioritas \+ Keuangan ───────────────────────\n    left, right = st\.columns\(\[3, 2\]\)\n\n    # ---- Daftar prioritas beli ----\n    with left:\n"
    content = re.sub(pattern1, "    # ── Konten utama: Prioritas Belanja ───────────────────────\n", content)
    
    # We need to unindent lines from ui.section_header(icons.icon_shopping_cart... down to the end of the dataframe
    lines = content.split('\n')
    in_table = False
    new_lines = []
    
    for line in lines:
        if line.strip() == 'ui.section_header(icons.icon_shopping_cart(24), "Prioritas Belanja")':
            in_table = True
        
        if in_table and line.strip() == '# ---- Keuangan ----':
            in_table = False
            
        if in_table:
            if line.startswith('    '):
                new_lines.append(line[4:])
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    content = '\n'.join(new_lines)

    # Replace the "with right:" block with "left_chart, right_chart = st.columns(2)"
    pattern2 = r"    # ---- Keuangan ----\n    with right:\n"
    replacement2 = "    st.markdown(\"<br>\", unsafe_allow_html=True)\n    # ── Keuangan & Kategori ───────────────────────\n    left_chart, right_chart = st.columns(2)\n    with left_chart:\n"
    content = re.sub(pattern2, replacement2, content)

    # Now, find the "ym = mf.iloc[-1]["bulan"]" block
    # It starts at:
    #             ym = mf.iloc[-1]["bulan"]
    #             exp_cat = db.get_expense_by_category(user_id, ym)
    #             if not exp_cat.empty:
    #                 st.caption(f"Pengeluaran per kategori ({ym})")
    #                 fig2 = px.bar(
    # ... down to
    #                 st.plotly_chart(fig2, use_container_width=True)
    
    # Let's extract that block, delete it from left_chart, and place it in right_chart.
    
    # Find the block indices
    lines = content.split('\n')
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if 'ym = mf.iloc[-1]["bulan"]' in line:
            start_idx = i
        if start_idx != -1 and 'st.plotly_chart(fig2, use_container_width=True)' in line:
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        extracted_block = lines[start_idx:end_idx+1]
        del lines[start_idx:end_idx+1]
        
        # We need to insert right_chart logic.
        # But wait, where should we put `with right_chart:`?
        # The left_chart ends right before the extracted block.
        # So we can insert it at start_idx.
        
        # But we also need to handle the case if mf is empty!
        # Because we want the right chart to say something if mf is empty, or just show the same as left chart.
        # Actually, let's just make it simple:
        
        right_chart_code = [
            "    with right_chart:",
            "        ui.section_header(icons.icon_pie_chart(24), \"Kategori Pengeluaran\")",
            "        if mf.empty:",
            "            st.info(\"Belum ada data pengeluaran.\")",
            "        else:"
        ]
        
        # The extracted block is indented by 12 spaces. We want it to be inside `else:` which is 12 spaces.
        # Perfect, no need to change indentation of extracted block!
        
        # Change `st.caption` to nothing because we have section header now
        new_extracted = []
        for line in extracted_block:
            if 'st.caption' in line:
                continue
            new_extracted.append(line)
            
        lines[start_idx:start_idx] = right_chart_code + new_extracted
        
    with open('views/dashboard.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    refactor()
