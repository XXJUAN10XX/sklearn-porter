# %% [markdown]
# # sklearn-porter
#
# Repository: [https://github.com/nok/sklearn-porter](https://github.com/nok/sklearn-porter)
#
# ## BernoulliNB
#
# Documentation: [sklearn.naive_bayes.BernoulliNB](http://scikit-learn.org/stable/modules/generated/sklearn.naive_bayes.BernoulliNB.html)

# %%
import sys
sys.path.append('../../../../..')

# %% [markdown]
# ### Load data

# %%
from sklearn.datasets import load_iris

iris_data = load_iris()

X = iris_data.data
y = iris_data.target

print(X.shape, y.shape)

# %% [markdown]
# ### Train classifier

# %%
from sklearn.naive_bayes import BernoulliNB

clf = BernoulliNB()
clf.fit(X, y)

# %% [markdown]
# ### Transpile classifier

# %%
from sklearn_porter import Porter

porter = Porter(clf, language='java')
output = porter.export()

print(output)

# %% [markdown]
# ### Run classification in Java

# %%
# Save classifier:
# with open('BernoulliNB.java', 'w') as f:
#     f.write(output)

# Compile model:
# $ javac -cp . BernoulliNB.java

# Run classification:
# $ java BernoulliNB 1 2 3 4
