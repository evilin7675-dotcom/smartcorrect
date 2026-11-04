"""Settings window (tkinter) with four tabs: Rules, Expansions, Settings, Log."""

import tkinter as tk
from tkinter import messagebox, ttk


class SettingsWindow:
    def __init__(self, store, on_change, hook=None):
        self.store = store
        self.on_change = on_change   # reload the engine after an edit
        self.hook = hook
        self.root = tk.Tk()
        self.root.title("SmartCorrect")
        self.root.geometry("560x420")

        tabs = ttk.Notebook(self.root)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)
        self.rules_tree = self._pair_tab(tabs, "Rules", ("Typo", "Correction"),
                                         store.rules, store.set_rule, store.delete_rule)
        self.exp_tree = self._pair_tab(tabs, "Expansions", ("Trigger", "Text"),
                                       store.expansions, store.set_expansion,
                                       store.delete_expansion)
        self._settings_tab(tabs)
        self._log_tab(tabs)

    def run(self):
        self.root.mainloop()

    # ---- tabs ---------------------------------------------------------------------
    def _pair_tab(self, tabs, title, headings, load, save, delete):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text=title)
        tree = ttk.Treeview(frame, columns=headings, show="headings", height=12)
        for h in headings:
            tree.heading(h, text=h)
            tree.column(h, width=240)
        tree.pack(fill="both", expand=True)

        form = ttk.Frame(frame)
        form.pack(fill="x", pady=6)
        key_entry, value_entry = ttk.Entry(form, width=18), ttk.Entry(form, width=30)
        key_entry.pack(side="left", padx=2)
        value_entry.pack(side="left", padx=2)

        def refresh():
            tree.delete(*tree.get_children())
            for k, v in load().items():
                tree.insert("", "end", values=(k, v.replace("\n", " / ")))

        def add():
            k, v = key_entry.get().strip(), value_entry.get()
            if not k or not v:
                messagebox.showwarning("SmartCorrect", "Fill in both boxes.")
                return
            save(k, v)
            key_entry.delete(0, "end")
            value_entry.delete(0, "end")
            refresh()
            self.on_change()

        def remove():
            for item in tree.selection():
                delete(tree.item(item, "values")[0])
            refresh()
            self.on_change()

        ttk.Button(form, text="Add or update", command=add).pack(side="left", padx=2)
        ttk.Button(form, text="Delete selected", command=remove).pack(side="left", padx=2)
        refresh()
        return tree

    def _settings_tab(self, tabs):
        frame = ttk.Frame(tabs, padding=12)
        tabs.add(frame, text="Settings")
        self.auto_cap = tk.BooleanVar(value=self.store.get_setting("auto_capitalise", "1") == "1")
        self.enabled = tk.BooleanVar(value=True)

        def save():
            self.store.set_setting("auto_capitalise", "1" if self.auto_cap.get() else "0")
            if self.hook:
                self.hook.enabled = self.enabled.get()
            self.on_change()

        ttk.Checkbutton(frame, text="Correct as I type", variable=self.enabled,
                        command=save).pack(anchor="w", pady=4)
        ttk.Checkbutton(frame, text="Capitalise the first word of each sentence",
                        variable=self.auto_cap, command=save).pack(anchor="w", pady=4)
        ttk.Label(frame, text="Ctrl+Alt+Z undoes the last correction.\n"
                              "Ctrl+Alt+P pauses or resumes SmartCorrect.").pack(anchor="w", pady=12)

    def _log_tab(self, tabs):
        frame = ttk.Frame(tabs)
        tabs.add(frame, text="Log")
        cols = ("Time", "Kind", "Before", "After")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=14)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130)
        tree.pack(fill="both", expand=True)

        def refresh():
            tree.delete(*tree.get_children())
            for row in self.store.recent():
                tree.insert("", "end", values=row)

        ttk.Button(frame, text="Refresh", command=refresh).pack(pady=6)
        refresh()
