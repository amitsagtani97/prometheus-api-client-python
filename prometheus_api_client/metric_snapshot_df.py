"""A pandas.DataFrame subclass for Prometheus query response."""
from pandas import DataFrame
from pandas._typing import Axes, Dtype
from typing import Optional, Sequence


class MetricSnapshotDataFrame(DataFrame):
    """Subclass to format and represent Prometheus query response as pandas.DataFrame.

    Assumes response is either a json or sequence of jsons.

    This is different than passing raw list of jsons to pandas.DataFrame in that it
    unpacks metric label values, extracts (first or last) timestamp-value pair (if
    multiple pairs are retuned), and concats them before passing to the pandas
    DataFrame constructor.

    :param data: (list|json) A single metric (json with keys "metric" and
                 "values"/"value") or list of such metrics received from Prometheus as
                 a response to query
    :param ts_values_keep: (str) If several timestamp-value tuples are returned for a
                 given metric + label config, determine which one to keep. Currently
                 only supports 'first', 'last'.
    :param args : same args as pandas.DataFrame constructor
    :param kwargs : same kwargs as pandas.DataFrame constructor

    Example Usage:
      .. code-block:: python

          prom = PrometheusConnect()
          metric_data = prom.get_current_metric_value(metric_name='up', label_config=my_label_config)
          metric_df = MetricSnapshotDataFrame(metric_data)
          metric_df.head()
          '''
          +-------------------------+-----------------+------------+-------+
          | __name__ | cluster      | label_2         | timestamp  | value |
          +==========+==============+=================+============+=======+
          | up       | cluster_id_0 | label_2_value_2 | 1577836800 | 0     |
          +-------------------------+-----------------+------------+-------+
          | up       | cluster_id_1 | label_2_value_3 | 1577836800 | 1     |
          +-------------------------+-----------------+------------+-------+
          '''

    """

    def __init__(
        self,
        data=None,
        ts_values_keep: str = 'last',
        index: Optional[Axes] = None,
        columns: Optional[Axes] = None,
        dtype: Optional[Dtype] = None,
        copy: bool = False,
    ):
        """Constructor for MetricSnapshotDataFrame class."""
        if data is not None:
            # if just a single json instead of list/set/other sequence of jsons,
            # treat as list with single entry
            if not isinstance(data, Sequence):
                data = [data]

            if ts_values_keep not in ("first", "last"):
                raise ValueError("ts_values_keep must be one of 'first' and 'last'")

            # index corresponding to which ts-value pair to extract
            n = -1 if ts_values_keep == "last" else 0

            # unpack metric, extract and unpack ts-value pair
            data = [
                {**i["metric"], **MetricSnapshotDataFrame._get_nth_ts_value_pair(i, n)}
                for i in data
            ]

        # init df normally now
        super(MetricSnapshotDataFrame, self).__init__(
            data=data, index=index, columns=columns, dtype=dtype, copy=copy
        )

    @staticmethod
    def _get_nth_ts_value_pair(i: dict, n: int):
        val = i["values"][n] if "values" in i else i["value"]
        return {"timestamp": val[0], "value": val[1]}
