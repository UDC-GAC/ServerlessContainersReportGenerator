# Copyright (c) 2019 Universidade da Coruña
# Authors:
#     - Jonatan Enes [main](jonatan.enes@udc.es, jonatan.enes.alvarez@gmail.com)
#     - Roberto R. Expósito
#     - Juan Touriño
#
# This file is part of the BDWatchdog framework, from
# now on referred to as BDWatchdog.
#
# BDWatchdog is free software: you can redistribute it
# and/or modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# BDWatchdog is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with BDWatchdog. If not, see <http://www.gnu.org/licenses/>.
from tabulate import tabulate

from src.common.utils import get_times_from_doc


def print_latex_section(section_name, section_label=None):
    if not section_label:
        section_label = section_name.replace(" ", "_")
    print("\\section{" + section_name + "}\label{" + section_label + "}")
    print("")

def print_basic_doc_info(doc):
    start_time_string, end_time_string, duration, duration_minutes = get_times_from_doc(doc)
    if "test_name" in doc:
        latex_print("\\textbf{TEST:}" + " {0}".format(doc["test_name"]))
    else:
        latex_print("\\textbf{EXPERIMENT:}" + " {0}".format(doc["experiment_id"]))
        latex_print("\\textbf{USER:}" + "{0}".format(doc["username"]))

    latex_print("\\textbf{START TIME:}" + " {0}".format(start_time_string))
    latex_print("\\textbf{END TIME:}" + " {0}".format(end_time_string))
    latex_print("\\textbf{DURATION:}" + " {0} seconds (about {1} minutes)".format(duration, duration_minutes) + "  ")


def flush_table(table, header, table_caption=None):
    # print_latex_vertical_space()
    print(tabulate(table, header))
    print("")
    if table_caption:
        latex_print("Table: " + table_caption)

# def print_latex_vertical_space():
#     print("\\vspace{-0.3cm}")
#     print("")


def print_latex_stress(s):
    # Print the \newline string so that it is detected as a Latex newline
    # print(str + "\\newline")
    # print two additional spaces so that it is detected by markdown and pandoc as a newline
    print("\\textbf{" + s + "}" + "  ")
    print("")


def latex_print(s):
    # Print the \newline string so that it is detected as a Latex newline
    # print(str + "\\newline")
    # print two additional spaces so that it is detected by markdown and pandoc as a newline
    print(s + "  ")
    print("")
