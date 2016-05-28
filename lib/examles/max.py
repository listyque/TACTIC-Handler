from PySide import QtGui
import MaxPlus

class _GCProtector(object):
	widgets = []
    
def make_cylinder():
	obj = MaxPlus.Factory.CreateGeomObject(MaxPlus.ClassIds.Cylinder)
	obj.ParameterBlock.Radius.Value = 10.0
	obj.ParameterBlock.Height.Value = 30.0
	node = MaxPlus.Factory.CreateNode(obj)
	time = MaxPlus.Core.GetCurrentTime()
	MaxPlus.ViewportManager.RedrawViews(time)

	return

app = QtGui.QApplication.instance()
if not app:
	app = QtGui.QApplication([])
	
def main():		
	MaxPlus.FileManager.Reset(True)
	w = QtGui.QWidget()
	w.resize(250, 100)
	w.setWindowTitle('Window')
	_GCProtector.widgets.append(w)
	w.show()

	main_layout = QtGui.QVBoxLayout()
	label = QtGui.QLabel("Click button to create a cylinder in the scene")
	main_layout.addWidget(label)

	cylinder_btn = QtGui.QPushButton("Cylinder")
	main_layout.addWidget(cylinder_btn)
	w.setLayout(main_layout)

	cylinder_btn.clicked.connect(make_cylinder)
	
if __name__ == '__main__':
	main()