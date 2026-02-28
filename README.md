## pyModRev: A Python Tool for Model Revision in Boolean Networks

**pyModRev** is a Python-based reimplementation of [ModRev](https://github.com/FilipeGouveia/ModRev), a tool for automated **consistency checking** and **repair** of Boolean network models using **Answer Set Programming (ASP)**. Given a Boolean model and a set of experimental observations (steady-state or time-series), pyModRev determines whether the model explains the data. If inconsistencies are found, it identifies **minimal repair operations** to fix the model.

Built on top of the [Clingo](https://potassco.org/clingo/) ASP solver and the [`pyfunctionhood`](https://github.com/ptgm/pyfunctionhood) library, pyModRev brings modern usability and extensibility to the model revision process by offering:

* ✅ **Full parity with ModRev's core logic**, using the same ASP encodings
* 🧩 **Modular architecture** with pluggable update policies (synchronous, asynchronous, complete, steady-state)
* 🐍 **Pure Python interface**, ideal for integration with scientific workflows
* 📁 **In-memory model and observation management**, enabling multiple consistency checks without reloading
* ⚙️ **Command-line interface** for batch processing and reproducibility

---
### Install

You need to install some dependencies using pip.

If your distribution prevents you to install pip packages system-wide,
please first create a Python environment:
```
$ python -m venv venv
$ source venv/bin/activate
```

Then install the dependencies simply by:
```
$ pip install -r requirements.txt
```

To run all the tests (using the created `venv` environment)
```
$ venv/bin/python3 -m pytest tests/ -v
```


---

### Getting Started

To run pyModRev:

```bash
$ python3 main.py -m <model_file.lp> -obs <observation.lp> <updater> [options]
```
