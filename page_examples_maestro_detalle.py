from pandas import DataFrame
import numpy as np
import streamlit as st
df = DataFrame(
    {
        "Animal": ["Lion", "Elephant", "Giraffe", "Monkey", "Zebra"],
        "Class": ["Mammal", "Mammal", "Mammal", "Mammal", "Mammal"],
        "Habitat": ["Savanna", "Forest", "Savanna", "Forest", "Savanna"],
        "Lifespan (years)": [15, 60, 25, 20, 25],
        "Average weight (kg)": [190, 5000, 800, 10, 350],
    }
)


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    # inserta una columna en el indice 0 con nombre 'Select' y valor false por defecto
    df_with_selections.insert(0, "Select", False)
    edited_df = st.data_editor(df_with_selections)
    #  condición para filtrar valores true de la columna 'Select' es decir, las filas seleccionadas.
    selected_indices = list(np.where(edited_df.Select)[0])
    selected_rows = df[edited_df.Select]
    return {"selected_rows_indices": selected_indices, "selected_rows": selected_rows}


selection = dataframe_with_selections(df)
st.write("Your selection:")
st.write(selection)