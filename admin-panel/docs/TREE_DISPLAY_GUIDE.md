# 🌳 Руководство по отображению дерева в Streamlit

Это руководство описывает различные способы отображения иерархических данных (деревьев) в Streamlit.

## 📋 Содержание

1. [Базовые способы](#базовые-способы)
2. [Интерактивные компоненты](#интерактивные-компоненты)
3. [Примеры кода](#примеры-кода)
4. [Рекомендации](#рекомендации)

## 🎯 Базовые способы

### 1. Expander (раскрывающиеся блоки)

**Преимущества:**
- Встроенный в Streamlit
- Простота использования
- Хорошая производительность

**Недостатки:**
- Ограниченная интерактивность
- Нельзя выбирать элементы

```python
def display_tree_expander(data, level=0):
    if isinstance(data, dict):
        name = data.get('name', 'Без названия')
        icon = "📁" if data.get('children') else "📄"
        
        with st.expander(f"{'  ' * level}{icon} {name}", expanded=level < 2):
            if 'children' in data and data['children']:
                for child in data['children']:
                    display_tree_expander(child, level + 1)
```

### 2. Markdown (текстовый список)

**Преимущества:**
- Простота
- Хорошая читаемость
- Поддержка форматирования

**Недостатки:**
- Нет интерактивности
- Ограниченные возможности стилизации

```python
def display_tree_markdown(data, level=0):
    if isinstance(data, dict):
        name = data.get('name', 'Без названия')
        icon = "📁" if data.get('children') else "📄"
        indent = "  " * level
        
        st.markdown(f"{indent}{icon} **{name}**")
        
        if 'children' in data and data['children']:
            for child in data['children']:
                display_tree_markdown(child, level + 1)
```

### 3. JSON Viewer

**Преимущества:**
- Полная информация о структуре
- Встроенный в Streamlit
- Поддержка сворачивания/разворачивания

**Недостатки:**
- Не очень удобно для больших деревьев
- Технический вид

```python
st.json(tree_data)
```

## 🎮 Интерактивные компоненты

### 4. Streamlit Tree Select

**Установка:**
```bash
pip install streamlit-tree-select
```

**Преимущества:**
- Полная интерактивность
- Выбор элементов
- Красивый интерфейс
- Поддержка чекбоксов

**Недостатки:**
- Дополнительная зависимость
- Ограниченная кастомизация

```python
from streamlit_tree_select import tree_select

def display_tree_select(data):
    tree_data = convert_to_tree_select_format(data)
    
    selected = tree_select(
        tree_data,
        show_expand_all=True,
        show_select_all=True,
        check_on_click=True
    )
    
    if selected:
        st.write("Выбранные элементы:", selected)

def convert_to_tree_select_format(data):
    if isinstance(data, dict):
        node = {
            "label": data.get('name', 'Без названия'),
            "value": data.get('name', ''),
            "icon": "📁" if data.get('children') else "📄"
        }
        
        if data.get('children'):
            node["children"] = [convert_to_tree_select_format(child) for child in data['children']]
        
        return node
    return data
```

## 📊 Дополнительные возможности

### 5. Метрики и статистика

```python
def display_tree_metrics(data):
    stats = analyze_tree_stats(data)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📁 Всего элементов", stats['total_items'])
    
    with col2:
        st.metric("📂 Папок", stats['folders'])
    
    with col3:
        st.metric("📄 Файлов", stats['files'])
    
    with col4:
        st.metric("📊 Максимальная глубина", stats['max_depth'])
```

### 6. Комбинированный подход с вкладками

```python
def show_tree_with_tabs(data):
    tabs = st.tabs([
        "🌳 Древовидное отображение", 
        "📋 Список", 
        "🔍 JSON", 
        "📊 Статистика"
    ])
    
    with tabs[0]:
        display_tree_expander(data)
    
    with tabs[1]:
        display_tree_markdown(data)
    
    with tabs[2]:
        st.json(data)
    
    with tabs[3]:
        display_tree_metrics(data)
```

## 🎨 Рекомендации

### Выбор способа отображения

1. **Для простого просмотра:** Используйте Expander или Markdown
2. **Для интерактивности:** Используйте Tree Select
3. **Для отладки:** Используйте JSON Viewer
4. **Для анализа:** Добавьте метрики и статистику

### Производительность

- Для больших деревьев (>1000 элементов) используйте ленивую загрузку
- Ограничивайте глубину отображения по умолчанию
- Используйте кэширование для часто используемых данных

### UX/UI советы

- Добавляйте иконки для разных типов элементов
- Используйте цветовое кодирование для уровней
- Предоставляйте возможность поиска
- Добавляйте хлебные крошки для навигации

## 🔧 Примеры использования в проекте

В файле `topics_and_tasks_page.py` реализованы все основные способы отображения дерева тем:

1. **Древовидное отображение** - с помощью expander'ов
2. **Интерактивное дерево** - с помощью streamlit-tree-select
3. **Список** - в виде markdown
4. **JSON** - для технического просмотра
5. **Статистика** - с метриками и анализом

## 📦 Установка зависимостей

```bash
pip install streamlit-tree-select
```

Или добавьте в `requirements.txt`:
```
streamlit-tree-select>=0.0.5
```

## 🚀 Быстрый старт

1. Скопируйте функции из `tree_examples.py`
2. Адаптируйте под ваши данные
3. Выберите подходящий способ отображения
4. Добавьте интерактивность при необходимости

## 📚 Дополнительные ресурсы

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Streamlit Tree Select](https://github.com/blackary/streamlit-tree-select)
- [Streamlit Components](https://docs.streamlit.io/library/api-reference/components)
