"""
Streamlit UI for Officials Tracker
"""
import streamlit as st
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.storage import StorageManager
from src.core.models import Mention, Person, Position, PositionAssignment, Department, Subdepartment, generate_mention_id
from datetime import datetime
import config

# Page config
st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout='wide'
)

# Initialize storage
# Use cache_resource for Streamlit 1.23+, fallback to experimental_singleton for older versions
try:
    @st.cache_resource
    def get_storage():
        return StorageManager(config.BASE_PATH)
except AttributeError:
    # Fallback for older Streamlit versions
    @st.experimental_singleton
    def get_storage():
        return StorageManager(config.BASE_PATH)

storage = get_storage()

# Helper function for displaying position with action buttons
def display_position_with_actions(pos, storage, persons):
    """Display a position with current holder and action buttons"""
    # Colored status label
    if pos.is_active:
        status = ':green[[Активна]]'
    else:
        status = ':red[[Неактивна]]'
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"{status} **{pos.title}** `{pos.id}`")
        
        # Get current holder
        current_persons = storage.get_persons_by_position(pos.id, current_only=True)
        if current_persons:
            for person in current_persons:
                current_pos_assignment = person.get_current_position()
                if current_pos_assignment and current_pos_assignment.position_id == pos.id:
                    st.markdown(f"   **{person.name}** (с {current_pos_assignment.start_date or '?'})")
        else:
            st.markdown(f"   *(вакантна)*")
    
    with col2:
        # Action buttons
        if pos.is_active:
            if st.button("Назначить", key=f"assign_{pos.id}", help="Назначить/Сменить лицо"):
                st.session_state[f'show_assign_{pos.id}'] = True
            
            if st.button("Деактивировать", key=f"deactivate_{pos.id}", help="Деактивировать позицию"):
                pos.is_active = False
                storage.update_position(pos)
                st.success("Позиция деактивирована")
                st.rerun()
    
    # Assignment modal
    if st.session_state.get(f'show_assign_{pos.id}'):
        with st.form(f"assign_form_{pos.id}"):
            st.markdown(f"#### Назначить на позицию: {pos.title}")
            
            # Check if someone currently holds this position
            current_holder = None
            current_persons_check = storage.get_persons_by_position(pos.id, current_only=True)
            if current_persons_check:
                current_holder = current_persons_check[0]
            
            if current_holder:
                st.warning(f"Сейчас: {current_holder.name}")
                st.markdown("Выберите действие:")
                action = st.radio("", ["Сменить лицо", "Добавить нового (если позиция может быть у нескольких)"], key=f"action_{pos.id}")
            else:
                action = "Назначить нового"
                st.info("Позиция вакантна")
            
            # Select or create person
            all_persons = storage.load_persons()
            person_options = ["Создать новое лицо"] + [f"{p.name} ({p.id})" for p in all_persons]
            selected_person = st.selectbox("Выберите лицо", person_options, key=f"person_{pos.id}")
            
            if selected_person == "Создать новое лицо":
                new_person_name = st.text_input("ФИО нового лица", key=f"new_name_{pos.id}")
            else:
                new_person_name = None
            
            start_date = st.date_input("Дата назначения", value=datetime.now().date(), key=f"date_{pos.id}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Назначить"):
                    # Close current holder if needed
                    if current_holder and action == "Сменить лицо":
                        for pos_assignment in current_holder.positions:
                            if pos_assignment.position_id == pos.id and pos_assignment.is_current:
                                pos_assignment.is_current = False
                                pos_assignment.end_date = str(start_date)
                        storage.update_person(current_holder)
                    
                    # Create new person if needed
                    if new_person_name:
                        person_id = storage.get_next_person_id()
                        person = Person(id=person_id, name=new_person_name, positions=[])
                    else:
                        person_id = selected_person.split('(')[-1].strip(')')
                        person = storage.get_person(person_id)
                    
                    # Add position assignment
                    person.add_position(
                        position_id=pos.id,
                        start_date=str(start_date),
                        end_date=None
                    )
                    storage.update_person(person)
                    
                    st.success(f"Назначен: {person.name}")
                    st.session_state[f'show_assign_{pos.id}'] = False
                    st.rerun()
            
            with col2:
                if st.form_submit_button("Отмена"):
                    st.session_state[f'show_assign_{pos.id}'] = False
                    st.rerun()
    
    st.markdown("")  # Spacing

# Sidebar navigation
st.sidebar.title("Officials Tracker")
page = st.sidebar.radio(
    "Навигация",
    ["Dashboard", 
     "Организационная структура",
     "Добавить упоминание", 
     "Персоны", 
     "Все упоминания"]
)

st.sidebar.markdown("---")
stats = storage.get_stats()
st.sidebar.markdown("### Статистика")
st.sidebar.metric("Позиций", stats['total_positions'])
st.sidebar.metric("Персон", stats['total_persons'])
st.sidebar.metric("Упоминаний", stats['total_mentions'])

# ==================== DASHBOARD ====================
if page == "Dashboard":
    st.title("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего позиций", stats['total_positions'])
        st.metric("Активных позиций", stats['active_positions'])
    
    with col2:
        st.metric("Всего персон", stats['total_persons'])
        st.metric("Текущих чиновников", stats['current_officials'])
    
    with col3:
        st.metric("Всего упоминаний", stats['total_mentions'])
    
    st.markdown("---")
    
    # Recent mentions
    st.subheader("Последние упоминания")
    recent_mentions = storage.get_all_mentions(limit=10)
    
    if recent_mentions:
        for mention in recent_mentions:
            person = storage.get_person(mention.person_id)
            person_name = person.name if person else mention.person_id
            
            with st.expander(f"{mention.date} - {person_name} - {mention.source}"):
                st.markdown(f"**Источник:** {mention.source}")
                if mention.url:
                    st.markdown(f"**URL:** {mention.url}")
                if mention.title:
                    st.markdown(f"**Заголовок:** {mention.title}")
                st.markdown(f"**Текст:**")
                st.text_area("", mention.text, height=150, key=f"text_{mention.id}", disabled=True)
                if mention.tags:
                    st.markdown(f"**Теги:** {', '.join(mention.tags)}")
    else:
        st.info("Упоминаний пока нет. Добавьте первое!")

# ==================== ORGANIZATIONAL STRUCTURE ====================
elif page == "Организационная структура":
    st.title("Организационная структура")
    
    # Action buttons at the top
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Создать ведомство", use_container_width=True):
            st.session_state['show_create_dept'] = True
    with col2:
        if st.button("Создать отдел", use_container_width=True):
            st.session_state['show_create_subdept'] = True
    with col3:
        if st.button("Создать позицию", use_container_width=True):
            st.session_state['show_create_position'] = True
    
    st.markdown("---")
    
    # Modals for creation
    if st.session_state.get('show_create_dept'):
        with st.form("create_department_form"):
            st.subheader("Создать новое ведомство")
            dept_name = st.text_input("Название ведомства", placeholder="Министерство...")
            dept_level = st.selectbox("Уровень", ["federal", "regional", "municipal"])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Создать"):
                    if dept_name:
                        st.success(f"Ведомство '{dept_name}' создано!")
                        st.session_state['show_create_dept'] = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Отмена"):
                    st.session_state['show_create_dept'] = False
                    st.rerun()
    
    if st.session_state.get('show_create_subdept'):
        positions = storage.load_positions()
        departments = sorted(list(set([p.department for p in positions])))
        
        with st.form("create_subdepartment_form"):
            st.subheader("Создать новый отдел/департамент")
            parent_dept = st.selectbox("В каком ведомстве?", departments)
            subdept_name = st.text_input("Название отдела", placeholder="Департамент...")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Создать"):
                    if subdept_name:
                        st.success(f"Отдел '{subdept_name}' создан в '{parent_dept}'!")
                        st.session_state['show_create_subdept'] = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Отмена"):
                    st.session_state['show_create_subdept'] = False
                    st.rerun()
    
    if st.session_state.get('show_create_position'):
        positions = storage.load_positions()
        departments = sorted(list(set([p.department for p in positions])))
        
        with st.form("create_position_quick_form"):
            st.subheader("Создать новую позицию")
            
            pos_dept = st.selectbox("Ведомство", departments)
            
            # Get subdepartments for selected department
            subdepts_in_dept = sorted(list(set([p.subdepartment for p in positions 
                                                if p.department == pos_dept and p.subdepartment])))
            # Add "Руководство" as first option if it exists
            if "Руководство" in subdepts_in_dept:
                subdepts_in_dept.remove("Руководство")
                subdepts_options = ["Руководство"] + subdepts_in_dept
            else:
                subdepts_options = ["Руководство"] + subdepts_in_dept
            
            pos_subdept = st.selectbox("Отдел/Департамент", subdepts_options)
            
            pos_title = st.text_input("Название позиции", placeholder="Директор департамента, Министр...")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Создать"):
                    if pos_title:
                        position_id = storage.get_next_position_id()
                        position = Position(
                            id=position_id,
                            title=pos_title,
                            department=pos_dept,
                            subdepartment=pos_subdept,  # Always set now
                            level='federal'
                        )
                        storage.add_position(position)
                        st.success(f"Позиция '{pos_title}' создана! ID: {position_id}")
                        st.session_state['show_create_position'] = False
                        st.rerun()
            with col2:
                if st.form_submit_button("Отмена"):
                    st.session_state['show_create_position'] = False
                    st.rerun()
    
    # Display structure
    st.markdown("---")
    st.subheader("Текущая структура")
    
    positions = storage.load_positions()
    persons = storage.load_persons()
    
    # Search
    search = st.text_input("Поиск по ведомству или позиции", "")
    
    if search:
        positions = [p for p in positions if 
                    search.lower() in p.title.lower() or 
                    search.lower() in p.department.lower() or
                    (p.subdepartment and search.lower() in p.subdepartment.lower())]
    
    # Group by department
    from collections import defaultdict
    by_dept = defaultdict(list)
    for pos in positions:
        by_dept[pos.department].append(pos)
    
    # Load departments and subdepartments status
    departments = storage.load_departments()
    subdepartments = storage.load_subdepartments()
    
    # Create lookup dicts
    dept_status = {d.name: d for d in departments}
    subdept_status = {(s.name, s.department_name): s for s in subdepartments}
    
    # Sort departments by active status (active first) then alphabetically
    sorted_depts = sorted(by_dept.items(), key=lambda x: (
        not (dept_status.get(x[0]).is_active if dept_status.get(x[0]) else True),  # Active first
        x[0]  # Then alphabetically
    ))
    
    for dept_name, dept_positions in sorted_depts:
        # Get department status
        dept_obj = dept_status.get(dept_name)
        dept_active = dept_obj.is_active if dept_obj else True
        
        # Colored status label
        if dept_active:
            dept_status_label = ':green[[Активно]]'
        else:
            dept_status_label = ':red[[Неактивно]]'
        
        # Department header with status and buttons
        col1, col2 = st.columns([4, 1])
        with col1:
            expander = st.expander(f"**{dept_name}** {dept_status_label} ({len(dept_positions)} позиций)", expanded=False)
        with col2:
            if dept_active:
                if st.button("Деактивировать", key=f"deact_dept_{dept_name}"):
                    if dept_obj:
                        dept_obj.is_active = False
                        dept_obj.deactivated_at = datetime.now().isoformat()
                        storage.update_department(dept_obj)
                        st.rerun()
            else:
                if st.button("Активировать", key=f"act_dept_{dept_name}"):
                    if dept_obj:
                        dept_obj.is_active = True
                        dept_obj.deactivated_at = None
                        storage.update_department(dept_obj)
                        st.rerun()
        
        with expander:
            # Group all positions by subdepartment
            by_subdept = defaultdict(list)
            for pos in dept_positions:
                by_subdept[pos.subdepartment].append(pos)
            
            # Sort subdepartments: "Руководство" first (if active), then by active status + alphabet
            subdepts = sorted(by_subdept.keys(), key=lambda x: (
                x != "Руководство",  # Руководство first
                not (subdept_status.get((x, dept_name)).is_active if subdept_status.get((x, dept_name)) else True),  # Active first
                x  # Then alphabetically
            ))
            
            for subdept_name in subdepts:
                subdept_positions = by_subdept[subdept_name]
                
                # Get subdepartment status
                subdept_obj = subdept_status.get((subdept_name, dept_name))
                subdept_active = subdept_obj.is_active if subdept_obj else True
                
                # Colored status label
                if subdept_active:
                    subdept_status_label = ':green[[Активно]]'
                else:
                    subdept_status_label = ':red[[Неактивно]]'
                
                # Subdepartment header with status and buttons
                col1, col2 = st.columns([4, 1])
                with col1:
                    subdept_expander = st.expander(f"**{subdept_name}** {subdept_status_label} ({len(subdept_positions)} позиций)")
                with col2:
                    if subdept_active:
                        if st.button("Деактивировать", key=f"deact_subdept_{dept_name}_{subdept_name}"):
                            if subdept_obj:
                                subdept_obj.is_active = False
                                subdept_obj.deactivated_at = datetime.now().isoformat()
                                storage.update_subdepartment(subdept_obj)
                                st.rerun()
                    else:
                        if st.button("Активировать", key=f"act_subdept_{dept_name}_{subdept_name}"):
                            if subdept_obj:
                                subdept_obj.is_active = True
                                subdept_obj.deactivated_at = None
                                storage.update_subdepartment(subdept_obj)
                                st.rerun()
                
                with subdept_expander:
                    # Sort positions by active status (active first) then alphabetically
                    sorted_positions = sorted(subdept_positions, key=lambda x: (not x.is_active, x.title))
                    
                    for pos in sorted_positions:
                        display_position_with_actions(pos, storage, persons)

# ==================== ADD MENTION ====================
elif page == "Добавить упоминание":
    st.title("➕ Добавить новое упоминание")
    
    # Load persons
    persons = storage.load_persons()
    if not persons:
        st.error("Нет персон в базе. Сначала добавьте персон.")
    else:
        # Create person selection
        person_options = {f"{p.name} ({p.id})": p for p in persons}
        
        selected_person_key = st.selectbox(
            "Выберите персону",
            options=list(person_options.keys()),
            key='person_select'
        )
        
        selected_person = person_options[selected_person_key]
        
        # Show current position
        current_pos = selected_person.get_current_position()
        if current_pos:
            pos = storage.get_position(current_pos.position_id)
            if pos:
                st.info(f"Текущая позиция: **{pos.title}** в {pos.department}")
        
        st.markdown("---")
        
        # Form
        with st.form("add_mention_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Дата", value=datetime.now())
                source = st.text_input("Источник", placeholder="Например: Коммерсантъ")
                url = st.text_input("URL", placeholder="https://...")
            
            with col2:
                title = st.text_input("Заголовок", placeholder="Заголовок статьи или сюжета")
                tags_input = st.text_input("Теги (через запятую)", placeholder="политика, экономика")
            
            text = st.text_area("Текст упоминания", height=300, placeholder="Вставьте текст упоминания здесь...")
            
            submitted = st.form_submit_button("Сохранить")
            
            if submitted:
                if not source or not text:
                    st.error("Заполните обязательные поля: Источник и Текст")
                else:
                    # Create mention
                    mention_id = generate_mention_id(selected_person.id, str(date))
                    
                    tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                    
                    mention = Mention(
                        id=mention_id,
                        person_id=selected_person.id,
                        date=str(date),
                        source=source,
                        url=url if url else None,
                        title=title if title else None,
                        text=text,
                        tags=tags,
                        collection_method='manual',
                        collected_by=config.CURRENT_USER
                    )
                    
                    # Save
                    try:
                        storage.save_mention(mention)
                        st.success(f"Упоминание сохранено! ID: {mention_id}")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Ошибка при сохранении: {e}")

# ==================== PERSONS ====================
elif page == "Персоны":
    st.title("👥 Управление персонами")
    
    tab1, tab2, tab3 = st.tabs(["Список", "Добавить персону", "Изменить позицию"])
    
    # Tab 1: List
    with tab1:
        persons = storage.load_persons()
        positions = storage.load_positions()
        positions_dict = {p.id: p for p in positions}
        
        if persons:
            # Search
            search = st.text_input("Поиск по имени", "")
            
            filtered_persons = persons
            if search:
                filtered_persons = [p for p in persons if search.lower() in p.name.lower()]
            
            st.markdown(f"Найдено персон: **{len(filtered_persons)}**")
            
            for person in filtered_persons:
                with st.expander(f"{person.name} ({person.id})"):
                    st.markdown("**История позиций:**")
                    
                    if person.positions:
                        for pos_assignment in person.positions:
                            pos = positions_dict.get(pos_assignment.position_id)
                            pos_title = pos.title if pos else pos_assignment.position_id
                            pos_dept = pos.department if pos else "Unknown"
                            
                            status = "[Активна] Текущая" if pos_assignment.is_current else "[Неактивна] Прошлая"
                            
                            st.markdown(f"""
                            - {status} **{pos_title}**
                              - Ведомство: {pos_dept}
                              - Период: {pos_assignment.start_date or '?'} → {pos_assignment.end_date or 'настоящее время'}
                            """)
                    else:
                        st.info("Нет позиций")
                    
                    # Mentions count
                    mentions = storage.load_mentions(person.id)
                    st.markdown(f"**Упоминаний:** {len(mentions)}")
        else:
            st.info("Персон пока нет")
    
    # Tab 2: Add person
    with tab2:
        st.subheader("Добавить новую персону")
        
        with st.form("add_person_form"):
            person_name = st.text_input("ФИО", placeholder="Иванов Иван Иванович")
            
            st.markdown("**Первая позиция (опционально):**")
            
            positions = storage.load_positions()
            position_options = ["Не назначать"] + [f"{p.title} - {p.department} ({p.id})" for p in positions]
            
            selected_position = st.selectbox("Позиция", position_options)
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Дата начала")
            with col2:
                is_current = st.checkbox("Текущая позиция", value=True)
                end_date = st.date_input("Дата окончания", disabled=is_current) if not is_current else None
            
            submitted = st.form_submit_button("Добавить персону")
            
            if submitted:
                if not person_name:
                    st.error("Введите ФИО")
                else:
                    person_id = storage.get_next_person_id()
                    
                    person = Person(
                        id=person_id,
                        name=person_name,
                        positions=[]
                    )
                    
                    # Add position if selected
                    if selected_position != "Не назначать":
                        pos_id = selected_position.split('(')[-1].strip(')')
                        person.add_position(
                            position_id=pos_id,
                            start_date=str(start_date),
                            end_date=str(end_date) if end_date else None
                        )
                    
                    try:
                        storage.add_person(person)
                        st.success(f"Персона добавлена! ID: {person_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Ошибка: {e}")
    
    # Tab 3: Change position
    with tab3:
        st.subheader("Изменить позицию персоны")
        
        persons = storage.load_persons()
        if persons:
            person_options = {f"{p.name} ({p.id})": p for p in persons}
            
            selected_person_key = st.selectbox(
                "Выберите персону",
                options=list(person_options.keys()),
                key='change_pos_person'
            )
            
            selected_person = person_options[selected_person_key]
            
            # Show current position
            st.markdown("**Текущие позиции:**")
            for pos_assignment in selected_person.positions:
                if pos_assignment.is_current:
                    pos = storage.get_position(pos_assignment.position_id)
                    if pos:
                        st.info(f"[Активна] {pos.title} в {pos.department}")
            
            st.markdown("---")
            
            with st.form("change_position_form"):
                action = st.radio("Действие", ["Добавить новую позицию", "Закрыть текущую позицию"])
                
                if action == "Добавить новую позицию":
                    positions = storage.load_positions()
                    position_options = [f"{p.title} - {p.department} ({p.id})" for p in positions]
                    
                    new_position = st.selectbox("Новая позиция", position_options)
                    start_date = st.date_input("Дата начала")
                    is_current = st.checkbox("Текущая позиция", value=True)
                    
                    submitted = st.form_submit_button("Сохранить")
                    
                    if submitted:
                        pos_id = new_position.split('(')[-1].strip(')')
                        selected_person.add_position(
                            position_id=pos_id,
                            start_date=str(start_date),
                            end_date=None if is_current else str(datetime.now().date())
                        )
                        
                        try:
                            storage.update_person(selected_person)
                            st.success("Позиция добавлена!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
                
                else:  # Close current position
                    end_date = st.date_input("Дата окончания", value=datetime.now())
                    
                    submitted = st.form_submit_button("Закрыть позицию")
                    
                    if submitted:
                        # Find current position and close it
                        for pos_assignment in selected_person.positions:
                            if pos_assignment.is_current:
                                pos_assignment.end_date = str(end_date)
                                pos_assignment.is_current = False
                        
                        try:
                            storage.update_person(selected_person)
                            st.success("Позиция закрыта!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Ошибка: {e}")
        else:
            st.info("Персон пока нет")

# ==================== POSITIONS ====================
# ==================== ALL MENTIONS ====================
elif page == "Все упоминания":
    st.title("Все упоминания")
    
    all_mentions = storage.get_all_mentions()
    
    if all_mentions:
        # Filters
        persons = storage.load_persons()
        person_dict = {p.id: p.name for p in persons}
        
        col1, col2 = st.columns(2)
        with col1:
            filter_person = st.selectbox(
                "Фильтр по персоне",
                ["Все"] + [f"{name} ({pid})" for pid, name in person_dict.items()]
            )
        with col2:
            filter_source = st.text_input("Фильтр по источнику", "")
        
        # Apply filters
        filtered = all_mentions
        if filter_person != "Все":
            person_id = filter_person.split('(')[-1].strip(')')
            filtered = [m for m in filtered if m.person_id == person_id]
        
        if filter_source:
            filtered = [m for m in filtered if filter_source.lower() in m.source.lower()]
        
        st.markdown(f"Найдено упоминаний: **{len(filtered)}**")
        
        # Display
        for mention in filtered:
            person_name = person_dict.get(mention.person_id, mention.person_id)
            
            with st.expander(f"{mention.date} - {person_name} - {mention.source}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Источник:** {mention.source}")
                    if mention.url:
                        st.markdown(f"**URL:** [{mention.url}]({mention.url})")
                    if mention.title:
                        st.markdown(f"**Заголовок:** {mention.title}")
                
                with col2:
                    st.markdown(f"**Персона:** {person_name}")
                    st.markdown(f"**Дата:** {mention.date}")
                    if mention.tags:
                        st.markdown(f"**Теги:** {', '.join(mention.tags)}")
                
                st.markdown("**Текст:**")
                st.text_area("", mention.text, height=150, key=f"all_text_{mention.id}", disabled=True)
    else:
        st.info("Упоминаний пока нет")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with  using Streamlit")
