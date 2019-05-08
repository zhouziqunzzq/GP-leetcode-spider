# LeetCode Spider
This is a part of Bittersweet's Graduation project.
It implements a simple spider with Python 3 to fetch
problems and problem data from LeetCode. It also
implements a Converter to convert LeetCode data
to TFRecord format for further usage.

## PIP dependencies
- requests
- lxml
- tensorflow (or tensorflow-gpu)

## Usage
```
python3 main.py [-h]
    [--method {normal,pairwise,pairwise_self_sim,pairwise_txt}]
    [--limit_length LIMIT_LENGTH]
    [--limit_question LIMIT_QUESTION]
    {fetch_data,convert_data}
```

## See also
- [MANN](https://github.com/zhouziqunzzq/GP-MANN)