from sklearn import pipeline, preprocessing
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
import pandas as pd
import numpy as np


def get_forest_model(data, categorical_data_columns, binary_data_columns, test_size=0.01):

    df = data.copy()
    df['Salary'] = df['Salary From']
    df = df.drop(['Salary From', 'Salary To'], axis=1)
    df = df[pd.notna(df['Salary'])]

    categorial_columns = df.columns[df.dtypes == np.object].tolist()
    encoders = {}
    for col_name in categorial_columns:
        encoders[col_name] = preprocessing.LabelEncoder()
        df[col_name] = encoders[col_name].fit_transform(df[col_name])

    (train_data, hold_out_test_data) = train_test_split(df, test_size=test_size, random_state=1)
    train_labels = train_data['Salary'].values
    train_data = train_data.drop(['Salary'], axis=1)
    test_labels = hold_out_test_data['Salary'].values
    test_data = hold_out_test_data.drop(['Salary'], axis=1)
    categorical_data_indices = np.array([column in categorical_data_columns for column in train_data.columns],
                                        dtype=bool)
    binary_data_indices = np.array([(column in binary_data_columns) for column in train_data.columns], dtype=bool)

    Model.train_data = train_data
    Model.train_labels = train_labels
    Model.test_data = test_data
    Model.test_labels = test_labels
    Model.binary_data_indices = binary_data_indices
    Model.categorical_data_indices = categorical_data_indices
    Model.test_size = test_size
    Model.encoders = encoders

    regressor = RandomForestRegressor(random_state=0)
    parameters_grid = {
        'model_fitting__n_estimators': [50],
        'model_fitting__max_features': ['sqrt'],
        'model_fitting__max_depth': [15]
    }
    model_forest = Model(regressor, parameters_grid)

    return model_forest


class Model(object):
    train_data = None
    train_labels = None
    test_data = None
    test_label = None
    binary_data_indices = None
    categorical_data_indices = None
    test_size = None
    encoders = None

    def __init__(self, regressor, parameters_grid):
        self.regressor = regressor
        self.parameters_grid = parameters_grid
        self.estimator = self.get_estimator()
        self.grid_cv = None
        self.test_predictions = None
        self.calc_grid()

    def get_estimator(self):
        binary = (
            'binary_variables_processing', preprocessing.FunctionTransformer(
                lambda data: data[:, Model.binary_data_indices], validate=True)
        )
        categorial = (
            'categorical_variables_processing',
            pipeline.Pipeline(
                steps=[
                    ('selecting', preprocessing.FunctionTransformer(
                        lambda data: data[:, Model.categorical_data_indices], validate=True)),
                    ('hot_encoding', preprocessing.OneHotEncoder(handle_unknown='ignore', sparse=False))
                ]
            )
        )
        estimator = pipeline.Pipeline(
            steps=[
                ('feature_processing', pipeline.FeatureUnion(transformer_list=[binary, categorial])),
                ('model_fitting', self.regressor)
            ]
        )
        return estimator

    def calc_grid(self):
        grid_cv = GridSearchCV(self.estimator, self.parameters_grid, cv=3)
        grid_cv.fit(self.train_data, self.train_labels)
        self.grid_cv = grid_cv
        self.test_predictions = self.grid_cv.best_estimator_.predict(self.test_data)

    # def view_model(self, count_head=20):
    #     val = (
    #         ('Модель на обучающей выборке: {}', (self.grid_cv.score(self.train_data, self.train_labels),)),
    #         ('Модель на тестовой выборке: {}', (self.grid_cv.score(self.test_data, Model.test_labels),)),
    #         ('Ошибка модели: {}',
    #          (metrics.mean_absolute_error(Model.test_labels, self.grid_cv.predict(self.test_data)),)),
    #         ('Факт(первые {}): {}', (count_head, Model.test_labels[:count_head])),
    #         ('Предсказание(первые {}): {}', (count_head, self.test_predictions[:count_head]))
    #     )
    #     for subs, data in val:
    #         print(subs.format(*data))

    def get_predict(self, data):
        for col_name in Model.encoders:
            data[col_name] = Model.encoders[col_name].transform(data[col_name])
        return self.grid_cv.predict(data)
