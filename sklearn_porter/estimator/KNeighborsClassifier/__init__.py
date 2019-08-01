# -*- coding: utf-8 -*-

from copy import deepcopy
from json import dumps, encoder
from logging import DEBUG
from textwrap import indent
from typing import Optional, Tuple, Union

# scikit-learn
from sklearn.neighbors.classification import \
    KNeighborsClassifier as KNeighborsClassifierClass

# sklearn-porter
from sklearn_porter.enums import Language, Method, Template
from sklearn_porter.estimator.EstimatorApiABC import EstimatorApiABC
from sklearn_porter.estimator.EstimatorBase import EstimatorBase
from sklearn_porter.exceptions import (
    NotFittedEstimatorError, NotSupportedYetError
)
from sklearn_porter.utils import get_logger

L = get_logger(__name__)


class KNeighborsClassifier(EstimatorBase, EstimatorApiABC):
    """Extract model data and port a KNeighborsClassifier classifier."""

    DEFAULT_LANGUAGE = Language.JAVA
    DEFAULT_TEMPLATE = Template.ATTACHED
    DEFAULT_METHOD = Method.PREDICT

    SUPPORT = {
        Language.JAVA: {
            Template.ATTACHED: {
                Method.PREDICT,
            },
            Template.EXPORTED: {
                Method.PREDICT,
            },
        },
        Language.JS: {
            Template.ATTACHED: {
                Method.PREDICT,
            },
            Template.EXPORTED: {
                Method.PREDICT,
            },
        },
    }

    estimator = None  # type: KNeighborsClassifierClass

    def __init__(self, estimator: KNeighborsClassifierClass):
        super().__init__(estimator)
        L.info('Create specific estimator `%s`.', self.estimator_name)
        est = self.estimator  # alias

        # Is the estimator fitted?
        try:
            est.classes_
        except AttributeError:
            raise NotFittedEstimatorError(self.estimator_name)

        if est.weights != 'uniform':
            msg = 'Only `uniform` weights are supported.'
            raise NotSupportedYetError(msg)

        self.meta_info = dict(
            n_classes=len(est.classes_),
            n_templates=len(est._fit_X),  # pylint: disable=W0212
            n_features=len(est._fit_X[0]),  # pylint: disable=W0212
            metric=est.metric
        )
        L.info('Meta info (keys): {}'.format(self.meta_info.keys()))
        if L.isEnabledFor(DEBUG):
            L.debug('Meta info: {}'.format(self.meta_info))

        self.model_data = dict(
            X=est._fit_X.tolist(),  # pylint: disable=W0212
            y=est._y.astype(int).tolist(),  # pylint: disable=W0212
            k=est.n_neighbors,  # number of relevant neighbors
            n=len(est.classes_),  # number of classes
            power=est.p
        )
        L.info('Model data (keys): {}'.format(self.model_data.keys()))
        if L.isEnabledFor(DEBUG):
            L.debug('Model data: {}'.format(self.model_data))

    def port(
        self,
        language: Optional[Language] = None,
        template: Optional[Template] = None,
        to_json: bool = False,
        **kwargs
    ) -> Union[str, Tuple[str, str]]:
        """
        Port an estimator.

        Parameters
        ----------
        language : Language
            The required language.
        template : Template
            The required template.
        to_json : bool (default: False)
            Return the result as JSON string.
        kwargs

        Returns
        -------
        The ported estimator.
        """
        method, language, template = self.check(
            language=language, template=template
        )

        # Arguments:
        kwargs.setdefault('method_name', method.value)
        converter = kwargs.get('converter')

        # Placeholders:
        plas = deepcopy(self.placeholders)  # alias
        plas.update(
            dict(
                class_name=kwargs.get('class_name'),
                method_name=kwargs.get('method_name'),
                to_json=to_json,
            )
        )
        plas.update(self.meta_info)

        # Templates:
        tpls = self._load_templates(language.value.KEY)

        # Export:
        if template == Template.EXPORTED:
            tpl_class = tpls.get_template('exported.class')
            out_class = tpl_class.render(**plas)
            converter = kwargs.get('converter')
            encoder.FLOAT_REPR = lambda o: converter(o)
            model_data = dumps(self.model_data, separators=(',', ':'))
            return out_class, model_data

        # Pick templates:
        tpl_int = tpls.get_template('int').render()
        tpl_double = tpls.get_template('double').render()
        tpl_arr_1 = tpls.get_template('arr[]')
        tpl_arr_2 = tpls.get_template('arr[][]')
        tpl_in_brackets = tpls.get_template('in_brackets')

        x_val = self.model_data.get('X')
        x_str = tpl_arr_2.render(
            type=tpl_double,
            name='X',
            values=', '.join(
                list(
                    tpl_in_brackets.render(
                        value=', '.join(list(map(converter, v)))
                    ) for v in x_val
                )
            ),
            n=len(x_val),
            m=len(x_val[0])
        )

        y_val = list(map(str, self.model_data.get('y')))
        y_str = tpl_arr_1.render(
            type=tpl_int, name='y', values=', '.join(y_val), n=len(y_val)
        )

        # Make class:
        tpl_class = tpls.get_template('attached.class')
        plas.update(
            dict(
                X=x_str,
                y=y_str,
                k=self.model_data.get('k'),
                n=self.model_data.get('n'),
                power=self.model_data.get('power'),
            )
        )
        out_class = tpl_class.render(**plas)
        return out_class
