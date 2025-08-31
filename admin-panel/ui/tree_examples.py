"""
Примеры различных способов отображения дерева в Streamlit
"""

import streamlit as st
import json

# Попытка импорта streamlit-tree-select
try:
    from streamlit_tree_select import tree_select

    TREE_SELECT_AVAILABLE = True
except ImportError:
    TREE_SELECT_AVAILABLE = False


def show_tree_examples():
    """Показать примеры отображения дерева"""
    st.header("🌳 Примеры отображения дерева в Streamlit")

    # Пример данных дерева
    sample_tree = {
        "name": "Корневая папка",
        "children": [
            {
                "name": "Документы",
                "children": [
                    {"name": "Отчет.pdf", "type": "file"},
                    {"name": "Презентация.pptx", "type": "file"},
                    {
                        "name": "Проекты",
                        "children": [{"name": "Проект А", "type": "folder"}, {"name": "Проект Б", "type": "folder"}],
                    },
                ],
            },
            {
                "name": "Изображения",
                "children": [{"name": "Фото 1.jpg", "type": "file"}, {"name": "Фото 2.png", "type": "file"}],
            },
        ],
    }

    # Создаем вкладки для разных способов отображения
    tabs = st.tabs(["1️⃣ Expander", "2️⃣ Markdown", "3️⃣ JSON", "4️⃣ Tree Select", "5️⃣ Метрики"])

    with tabs[0]:
        st.subheader("📁 Expander (раскрывающиеся блоки)")
        display_tree_expander(sample_tree)

    with tabs[1]:
        st.subheader("📝 Markdown (текстовый список)")
        display_tree_markdown(sample_tree)

    with tabs[2]:
        st.subheader("🔍 JSON Viewer")
        st.json(sample_tree)

    with tabs[3]:
        st.subheader("🎯 Tree Select (интерактивное дерево)")
        if TREE_SELECT_AVAILABLE:
            display_tree_select(sample_tree)
        else:
            st.warning("⚠️ streamlit-tree-select не установлен")
            st.code("pip install streamlit-tree-select")

    with tabs[4]:
        st.subheader("📊 Метрики дерева")
        display_tree_metrics(sample_tree)


def display_tree_expander(data, level=0):
    """Отобразить дерево с помощью expander'ов"""
    if isinstance(data, dict):
        name = data.get("name", "Без названия")
        icon = "📁" if data.get("children") else "📄"

        with st.expander(f"{'  ' * level}{icon} {name}", expanded=level < 2):
            if "type" in data:
                st.write(f"📋 Тип: {data['type']}")

            if "children" in data and data["children"]:
                st.write("📂 Содержимое:")
                for child in data["children"]:
                    display_tree_expander(child, level + 1)
            else:
                st.info("📭 Пустая папка")


def display_tree_markdown(data, level=0):
    """Отобразить дерево в виде markdown"""
    if isinstance(data, dict):
        name = data.get("name", "Без названия")
        icon = "📁" if data.get("children") else "📄"
        indent = "  " * level

        st.markdown(f"{indent}{icon} **{name}**")

        if "type" in data:
            st.markdown(f"{indent}  📋 Тип: {data['type']}")

        if "children" in data and data["children"]:
            for child in data["children"]:
                display_tree_markdown(child, level + 1)


def display_tree_select(data):
    """Отобразить интерактивное дерево"""
    if not TREE_SELECT_AVAILABLE:
        return

    # Преобразуем данные в формат для tree_select
    tree_data = convert_to_tree_select_format(data)

    # Отображаем интерактивное дерево
    selected = tree_select(tree_data, show_expand_all=True, show_select_all=True, check_on_click=True)

    if selected:
        st.write("✅ Выбранные элементы:", selected)


def convert_to_tree_select_format(data):
    """Преобразовать данные в формат для tree_select"""
    if isinstance(data, dict):
        node = {
            "label": data.get("name", "Без названия"),
            "value": data.get("name", ""),
            "icon": "📁" if data.get("children") else "📄",
        }

        if data.get("children"):
            node["children"] = [convert_to_tree_select_format(child) for child in data["children"]]

        return node
    return data


def display_tree_metrics(data):
    """Отобразить метрики дерева"""
    stats = analyze_tree_stats(data)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📁 Всего элементов", stats["total_items"])

    with col2:
        st.metric("📂 Папок", stats["folders"])

    with col3:
        st.metric("📄 Файлов", stats["files"])

    with col4:
        st.metric("📊 Максимальная глубина", stats["max_depth"])


def analyze_tree_stats(data, level=0, stats=None):
    """Анализировать дерево и собирать статистику"""
    if stats is None:
        stats = {"total_items": 0, "folders": 0, "files": 0, "max_depth": 0}

    if isinstance(data, dict):
        stats["total_items"] += 1
        stats["max_depth"] = max(stats["max_depth"], level)

        if data.get("children"):
            stats["folders"] += 1
            for child in data["children"]:
                analyze_tree_stats(child, level + 1, stats)
        else:
            stats["files"] += 1

    return stats


if __name__ == "__main__":
    show_tree_examples()
