from matplotlib import rcParams, cm, colors
from cycler import cycler

# https://github.com/vega/vega/wiki/Scales#scale-range-literals
cyc_10 = list(map(colors.to_hex, cm.tab10.colors))
cyc_20 = list(map(colors.to_hex, cm.tab20c.colors))

# ideally let us convert the following ggplot theme for Nature publisher group into matplotlib.rcParams
# nm_theme <- function() {
#   theme(strip.background = element_rect(colour = 'white', fill = 'white')) +
#     theme(panel.border = element_blank(), axis.line = element_line()) +
#     theme(panel.grid.minor.x = element_blank(), panel.grid.minor.y = element_blank()) +
#     theme(panel.grid.major.x = element_blank(), panel.grid.major.y = element_blank()) +
#     theme(panel.background = element_rect(fill='white')) +
#     #theme(text = element_text(size=6)) +
#     theme(axis.text.y=element_text(size=6)) +
#     theme(axis.text.x=element_text(size=6)) +
#     theme(axis.title.y=element_text(size=6)) +
#     theme(axis.title.x=element_text(size=6)) +
#     theme(panel.border = element_blank(), axis.line = element_line(size = .1), axis.ticks = element_line(size = .1)) +
#     theme(legend.position = "none") +
#     theme(strip.text.x = element_text(colour="black", size=6)) +
#     theme(strip.text.y = element_text(colour="black", size=6)) +
#     theme(legend.title = element_text(colour="black", size = 6)) +
#     theme(legend.text = element_text(colour="black", size = 6)) +
#     theme(plot.margin=unit(c(0,0,0,0), "lines"))
# }

def config_dynamo_rcParams(prop_cycle=cyc_20, fontsize=8, color_map=None, frameon=None):
    """Configure matplotlib.rcParams to dynamo defaults (based on ggplot style and scanpy).

    Parameters
    ----------
        prop_cycle: `list` (default: cyc_20)
            A list with hex color codes
        fontsize: float (default: 6)
            Size of font
        color_map: `plt.cm` or None (default: None)
            Color map
        frameon: `bool` or None (default: None)
            Whether to have frame for the figure.
    Returns
    -------
        Nothing but configure the rcParams globally.
    """

    # from http://www.huyng.com/posts/sane-color-scheme-for-matplotlib/

    rcParams['patch.linewidth'] = 0.5
    rcParams['patch.facecolor'] = "348ABD" # blue
    rcParams['patch.edgecolor'] = "EEEEEE"
    rcParams['patch.antialiased'] = True

    rcParams['font.size'] = 10.0

    rcParams['axes.facecolor'] = "E5E5E5"
    rcParams['axes.edgecolor'] = "white"
    rcParams['axes.linewidth'] = 1
    rcParams['axes.grid'] = True
    # rcParams['axes.titlesize'] =  "x-large"
    # rcParams['axes.labelsize'] = "large"
    rcParams['axes.labelcolor'] = "555555"
    rcParams['axes.axisbelow'] = True  # grid/ticks are below elements (e.g., lines, text)

    # rcParams['axes.prop_cycle'] = cycler('color', ['E24A33', '348ABD', '988ED5', '777777', 'FBC15E', '8EBA42', 'FFB5B8'])
    # # E24A33 : red
    # # 348ABD : blue
    # # 988ED5 : purple
    # # 777777 : gray
    # # FBC15E : yellow
    # # 8EBA42 : green
    # # FFB5B8 : pink

    # rcParams['xtick.color'] = "555555"
    rcParams['xtick.direction'] = "out"

    # rcParams['ytick.color'] = "555555"
    rcParams['ytick.direction'] = "out"

    rcParams['grid.color'] = "white"
    rcParams['grid.linestyle'] = "-"  # solid line

    rcParams['figure.facecolor'] = "white"
    rcParams['figure.edgecolor'] = "white" # 0.5

    # the following code is modified from scanpy
    # https://github.com/theislab/scanpy/blob/178a0981405ba8ccfd5031eb15bc07b3a45d2730/scanpy/plotting/_rcmod.py

    # dpi options (mpl default: 100, 100)
    rcParams['figure.dpi'] = 100
    rcParams['savefig.dpi'] = 160

    # figure (default: 0.125, 0.96, 0.15, 0.91)
    rcParams['figure.figsize'] = (6.5, 5)
    rcParams['figure.subplot.left'] = 0.18
    rcParams['figure.subplot.right'] = 0.96
    rcParams['figure.subplot.bottom'] = 0.15
    rcParams['figure.subplot.top'] = 0.91

    # lines (defaults:  1.5, 6, 1)
    rcParams['lines.linewidth'] = 1.5  # the line width of the frame
    rcParams['lines.markersize'] = 6
    rcParams['lines.markeredgewidth'] = 1

    # font
    rcParams['font.sans-serif'] = [
        'Helvetica',
        'Arial',
        'DejaVu Sans',
        'Bitstream Vera Sans',
        'sans-serif',
    ]
    fontsize = fontsize
    labelsize = 0.90 * fontsize

    # fonsizes (default: 10, medium, large, medium)
    rcParams['font.size'] = fontsize
    rcParams['legend.fontsize'] = labelsize
    rcParams['axes.titlesize'] = fontsize
    rcParams['axes.labelsize'] = labelsize

    # legend (default: 1, 1, 2, 0.8)
    rcParams['legend.numpoints'] = 1
    rcParams['legend.scatterpoints'] = 1
    rcParams['legend.handlelength'] = 0.5
    rcParams['legend.handletextpad'] = 0.4

    # color cycle
    rcParams['axes.prop_cycle'] = cycler(color=prop_cycle) # use tab20c by default

    # lines
    rcParams['axes.linewidth'] = 0.8
    rcParams['axes.edgecolor'] = 'black'
    rcParams['axes.facecolor'] = 'white'

    # ticks (default: k, k, medium, medium)
    rcParams['xtick.color'] = 'k'
    rcParams['ytick.color'] = 'k'
    rcParams['xtick.labelsize'] = labelsize
    rcParams['ytick.labelsize'] = labelsize

    # axes grid (default: False, #b0b0b0)
    rcParams['axes.grid'] = False
    rcParams['grid.color'] = '.8'

    # color map
    rcParams['image.cmap'] = (
        'RdBu_r' if color_map is None else color_map
    )

    # frame (default: True)
    frameon = False if frameon is None else frameon
    global _frameon
    _frameon = frameon


def set_figure_params(dynamo=True, fontsize=8, figsize=(6.5, 5), dpi=None, dpi_save=None, frameon=None, vector_friendly=True,
                      color_map=None, format='pdf', transparent=False, ipython_format='png2x'):
    """Set resolution/size, styling and format of figures.
       This function is adapted from: https://github.com/theislab/scanpy/blob/f539870d7484675876281eb1c475595bf4a69bdb/scanpy/_settings.py
    Arguments
    ---------
        dynamo: `bool` (default: `True`)
            Init default values for :obj:`matplotlib.rcParams` suited for dynamo.
        fontsize: `[float, float]` or None (default: `6`)
        figsize: `(float, float)` (default: `(6.5, 5)`)
            Width and height for default figure size.
        dpi: `int` or None (default: `None`)
            Resolution of rendered figures - this influences the size of figures in notebooks.
        dpi_save: `int` or None (default: `None`)
            Resolution of saved figures. This should typically be higher to achieve
            publication quality.
        frameon: `bool` or None (default: `None`)
            Add frames and axes labels to scatter plots.
        vector_friendly: `bool` (default: `True`)
            Plot scatter plots using `png` backend even when exporting as `pdf` or `svg`.
        color_map: `str` (default: `None`)
            Convenience method for setting the default color map.
        format: {'png', 'pdf', 'svg', etc.} (default: 'pdf')
            This sets the default format for saving figures: `file_format_figs`.
        transparent: `bool` (default: `False`)
            Save figures with transparent back ground. Sets `rcParams['savefig.transparent']`.
        ipython_format : list of `str` (default: 'png2x')
            Only concerns the notebook/IPython environment; see
            `IPython.core.display.set_matplotlib_formats` for more details.
    """

    try:
        import IPython
        if isinstance(ipython_format, str):
            ipython_format = [ipython_format]
        IPython.display.set_matplotlib_formats(*ipython_format)
    except Exception:
        pass

    from matplotlib import rcParams

    global _vector_friendly, file_format_figs

    _vector_friendly = vector_friendly
    file_format_figs = format

    if dynamo:
        config_dynamo_rcParams(fontsize=fontsize, color_map=color_map)
    if figsize is not None:
        rcParams['figure.figsize'] = figsize

    if dpi is not None:
        rcParams["figure.dpi"] = dpi
    if dpi_save is not None:
        rcParams["savefig.dpi"] = dpi_save
    if transparent is not None:
        rcParams["savefig.transparent"] = transparent
    if frameon is not None:
        global _frameon
        _frameon = frameon


def reset_rcParams():
    """Reset `matplotlib.rcParams` to defaults."""
    from matplotlib import rcParamsDefault
    rcParams.update(rcParamsDefault)
