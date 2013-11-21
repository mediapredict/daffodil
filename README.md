daffodil
========

data filtering lib

[![build status](https://travis-ci.org/mediapredict/daffodil.png)](https://travis-ci.org/mediapredict/daffodil)

[8/9/13, 12:45:04 PM] James Robert: for 18 year old women:

```
age = 18
gender = "female"
```

[8/9/13, 12:45:41 PM] James Robert: for men, 18 - 35:

```
gender = "male"
age >= 18
age <= 35
```

[8/9/13, 12:45:54 PM] James Robert: (this is what we'll use for MP)  
[8/9/13, 12:46:25 PM] James Robert: you can do OR rules instead of AND rules using "[]"  
[8/9/13, 12:47:02 PM] James Robert: people who are 18 years old or 21 years old:

```
[
age = 18
age = 21
]
```

[8/9/13, 12:47:36 PM] James Robert: women who are 18 or 21:

```
gender = "female"
[
  age = 18
  age = 21
]
```

[8/9/13, 12:48:11 PM] James Robert: this also works:

```
gender = "female"
[ age = 18, age = 21 ]
```

[8/9/13, 12:49:00 PM] James Robert: "{}" for AND  
[8/9/13, 12:50:14 PM] James Robert: women who are 18 or 21, or between 35 and 55:

```
gender = "female"
[
  age = 18
  age = 21
  {
    age >= 35
    age <= 55
  }
]
```

Quotes around the Field names are optional when the name is only letters, numbers, dashes, and underscores. The following three examples are all exactly equivalent:

```
gender = "female"
```

```
"gender" = "female"
```

```
'gender' = "female"
```

## Empty "AND" Blocks and "OR" blocks

An empty "AND" block will match **all** users

```
{}
```

An empty "OR" block will match **no** users

```
[]
```

This means you can set `{}` as your last filter in cases where you want to match various groups and then have an "everybody else" group.
