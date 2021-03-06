import numpy as np
import pandas as pd
from scipy.sparse import issparse, csr_matrix

from ..preprocessing.preprocess import topTable
from ..preprocessing.utilities import get_layer_keys


def show_fraction(adata, group=None):
    """Plot the fraction of each category of data used in the velocity estimation.

    Parameters
    ----------
    adata: :class:`~anndata.AnnData`
        an Annodata object
    group: `string` (default: None)
        Which group to facets the data into subplots. Default is None, or no faceting will be used.

    Returns
    -------
        A violin plot that shows the fraction of each category, produced by seaborn.
    """

    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_style('ticks')

    mode = None
    if pd.Series(['spliced', 'unspliced']).isin(adata.layers.keys()).all():
        mode = 'splicing'
    elif pd.Series(['new', 'total']).isin(adata.layers.keys()).all():
        mode = 'labelling'
    elif pd.Series(['uu', 'ul', 'su','sl']).isin(adata.layers.keys()).all():
        mode = 'full'

    if not (mode in ['labelling', 'splicing', 'full']):
        raise Exception("your data doesn't seem to have either splicing or labeling or both information")

    if mode is 'labelling':
        new_mat, total_mat = adata.layers['new'], adata.layers['total']

        new_cell_sum, tot_cell_sum = (np.sum(new_mat, 1), np.sum(total_mat, 1)) if not issparse(new_mat) else (new_mat.sum(1).A1, \
                                     total_mat.sum(1).A1)

        new_frac_cell = new_cell_sum / tot_cell_sum
        old_frac_cell = 1 - new_frac_cell
        df = pd.DataFrame({'new_frac_cell': new_frac_cell, 'old_frac_cell': old_frac_cell}, index=adata.obs.index)

        if group is not None and group in adata.obs.key():
            df['group'] = adata.obs[group]
            res = df.melt(value_vars=['new_frac_cell', 'old_frac_cell'], id_vars=['group'])
        else:
            res = df.melt(value_vars=['new_frac_cell', 'old_frac_cell'])

    elif mode is 'splicing':
        if 'ambiguous' in adata.layers.keys():
            ambiguous = adata.layers['ambiguous']
        else:
            ambiguous = csr_matrix(np.array([[0]])) if issparse(adata.layers['unspliced']) else np.array([[0]])

        unspliced_mat, spliced_mat, ambiguous_mat = adata.layers['unspliced'], adata.layers['spliced'], ambiguous
        un_cell_sum, sp_cell_sum = (np.sum(unspliced_mat, 1), np.sum(spliced_mat, 1)) if not \
            issparse(unspliced_mat) else (unspliced_mat.sum(1).A1, spliced_mat.sum(1).A1)

        if 'ambiguous' in adata.layers.keys():
            am_cell_sum = ambiguous_mat.sum(1).A1 if issparse(unspliced_mat) else np.sum(ambiguous_mat, 1)
            tot_cell_sum = un_cell_sum + sp_cell_sum + am_cell_sum
            un_frac_cell, sp_frac_cell, am_frac_cell = un_cell_sum / tot_cell_sum, sp_cell_sum / tot_cell_sum, am_cell_sum / tot_cell_sum
            df = pd.DataFrame({'unspliced': un_frac_cell, 'spliced': sp_frac_cell, 'ambiguous': am_frac_cell}, index=adata.obs.index)
        else:
            tot_cell_sum = un_cell_sum + sp_cell_sum
            un_frac_cell, sp_frac_cell = un_cell_sum / tot_cell_sum, sp_cell_sum / tot_cell_sum
            df = pd.DataFrame({'unspliced': un_frac_cell, 'spliced': sp_frac_cell}, index=adata.obs.index)

        if group is not None and group in adata.obs.columns:
            df['group'] = adata.obs.loc[:, group]
            res = df.melt(value_vars=['unspliced', 'spliced', 'ambiguous'], id_vars=['group']) if 'ambiguous' in adata.layers.keys() else \
                df.melt(value_vars=['unspliced', 'spliced'], id_vars=['group'])
        else:
            res = df.melt(value_vars=['unspliced', 'spliced', 'ambiguous']) if 'ambiguous' in adata.layers.keys() else \
                 df.melt(value_vars=['unspliced', 'spliced'])

    elif mode is 'full':
        uu, ul, su, sl = adata.layers['uu'], adata.layers['ul'], adata.layers['su'], adata.layers['sl']
        uu_sum, ul_sum, su_sum, sl_sum = np.sum(uu, 1), np.sum(ul, 1), np.sum(su, 1), np.sum(sl, 1) if not issparse(uu) \
            else uu.sum(1).A1, ul.sum(1).A1, su.sum(1).A1, sl.sum(1).A1

        tot_cell_sum = uu + ul + su + sl
        uu_frac, ul_frac, su_frac, sl_frac = uu_sum / tot_cell_sum, ul_sum / tot_cell_sum, su / tot_cell_sum, sl / tot_cell_sum
        df = pd.DataFrame({'uu_frac': uu_frac, 'ul_frac': ul_frac, 'su_frac': su_frac, 'sl_frac': sl_frac}, index=adata.obs.index)

        if group is not None and group in adata.obs.key():
            df['group'] = adata.obs[group]
            res = df.melt(value_vars=['uu_frac', 'ul_frac', 'su_frac', 'sl_frac'], id_vars=['group'])
        else:
            res = df.melt(value_vars=['uu_frac', 'ul_frac', 'su_frac', 'sl_frac'])

    if group is None:
        g = sns.violinplot(x="variable", y="value", data=res)
        g.set_xlabel('Category')
        g.set_ylabel('Fraction')
    else:
        g = sns.catplot(x="variable", y="value", data=res, kind='violin', col="group", col_wrap=4)
        g.set_xlabels('Category')
        g.set_ylabels('Fraction')

    plt.show()


def variance_explained(adata, threshold=0.002, n_pcs=None):
    """Plot the accumulative variance explained by the principal components.

    Parameters
    ----------
        adata: :class:`~anndata.AnnData`
        threshold: `float` (default: `0.002`)
            The threshold for the second derivative of the cumulative sum of the variance for each principal component.
            This threshold is used to determine the number of principal component used for downstream non-linear dimension
            reduction.
        n_pcs: `int` (default: `None`)
            Number of principal components.

    Returns
    -------
        Nothing but make a matplotlib based plot for showing the cumulative variance explained by each PC.
    """

    import matplotlib.pyplot as plt

    var_ = adata.uns["explained_variance_ratio_"]
    _, ax = plt.subplots()
    ax.plot(var_, c='k')
    tmp = np.diff(np.diff(np.cumsum(var_)) > threshold)
    n_comps = n_pcs if n_pcs is not None else np.where(tmp)[0][0] if np.any(tmp) else 20
    ax.axvline(n_comps, c="r")
    ax.set_xlabel('PCs')
    ax.set_ylabel('Variance explained')
    ax.set_xticks(list(ax.get_xticks()) + [n_comps])
    ax.set_xlim(0, len(var_))

    plt.show()


def feature_genes(adata, layer='X', mode=None):
    """Plot selected feature genes on top of the mean vs. dispersion scatterplot.

    Parameters
    ----------
        adata: :class:`~anndata.AnnData`
            AnnData object
        layer: `str` (default: `X`)
            The data from a particular layer (include X) used for making the feature gene plot.
        mode: None or `str` (default: `None`)
            The method to select the feature genes (can be either `dispersion`, `gini` or `SVR`).

    Returns
    -------
        Nothing but plots the selected feature genes via the mean, CV plot.
    """

    import matplotlib.pyplot as plt
    mode = adata.uns['feature_selection'] if mode is None else mode

    layer = get_layer_keys(adata, layer, include_protein=False)[0]
    if layer in ['raw', 'X']:
        key = 'dispFitInfo' if mode is 'dispersion' else 'velocyto_SVR'
    else:
        key = layer + '_dispFitInfo' if mode is 'dispersion' else layer + '_velocyto_SVR'

    if mode is 'dispersion':
        table = topTable(adata, layer)
        x_min, x_max = np.nanmin(table['mean_expression']), np.nanmax(table['mean_expression'])
    elif mode is 'SVR':
        if not np.all(pd.Series(['log_m', 'score']).isin(adata.var.columns)):
            raise Exception('Looks like you have not run support vector machine regression yet, try run SVRs first.')
        else:
            detected_bool = adata.uns[key]['detected_bool']
            table = adata.var.loc[detected_bool, ['log_m', 'log_cv', 'score']]
            table = table.loc[np.isfinite(table['log_m']) & np.isfinite(table['log_cv']), :]
            x_min, x_max = np.nanmin(table['log_m']), np.nanmax(table['log_m'])

    ordering_genes = adata.var['use_for_dynamo'] if 'use_for_dynamo' in adata.var.columns else None

    mu_linspace = np.linspace(x_min, x_max, num=1000)
    fit = adata.uns[key]['disp_func'](mu_linspace) if mode is 'dispersion' else adata.uns[key]['SVR'](mu_linspace.reshape(-1, 1))

    plt.plot(mu_linspace, fit, alpha=0.4, color='r')
    valid_ind = table.index.isin(ordering_genes.index[ordering_genes]) if ordering_genes is not None else np.ones(table.shape[0], dtype=bool)

    valid_disp_table = table.iloc[valid_ind, :]
    if mode is 'dispersion':
        plt.scatter(valid_disp_table['mean_expression'], valid_disp_table['dispersion_empirical'], s=3, alpha=1, color='xkcd:black')
    elif mode is 'SVR':
        plt.scatter(valid_disp_table['log_m'], valid_disp_table['log_cv'], s=3, alpha=1, color='xkcd:black')

    neg_disp_table = table.iloc[~valid_ind, :]

    if mode is 'dispersion':
        plt.scatter(neg_disp_table['mean_expression'], neg_disp_table['dispersion_empirical'], s=3, alpha=0.5, color='xkcd:grey')
    elif mode is 'SVR':
        plt.scatter(neg_disp_table['log_m'], neg_disp_table['log_cv'], s=3, alpha=0.5, color='xkcd:grey')

    # plt.xlim((0, 100))
    if mode is 'dispersion':
        plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Mean (log)')
    plt.ylabel('Dispersion (log)') if mode is 'dispersion' else plt.ylabel('CV (log)')
    plt.show()

