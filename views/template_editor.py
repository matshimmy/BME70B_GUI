from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import Qt

from models.template_model import TemplateModel

class TemplateEditor(QWidget):
    def __init__(self, template_model: TemplateModel):
        super().__init__()
        self.template_model = template_model
        self.dragging = False
        self.current_point_index = None
        self.plot_clicked_toggle = False
        
        # Connect to duration changes
        self.template_model.duration_changed.connect(self._on_duration_changed)
        
        self._build_ui()
        self._update_template()  # Initial display

    def _build_ui(self):
        layout = QVBoxLayout()
        
        # Create template plot
        self.template_plot = pg.PlotWidget()
        self.template_plot.setBackground('w')
        self.template_plot.setLabel('left', 'Amplitude', units='V')
        self.template_plot.setLabel('bottom', 'Time', units='ms')
        self.template_plot.setXRange(0, self.template_model._duration_ms)
        self.template_plot.setYRange(*self.template_model._y_range)
        
        # Add grid
        self.template_plot.showGrid(x=True, y=True, alpha=0.3)
        
        # Disable default mouse interactions
        self.template_plot.setMouseEnabled(x=False, y=False)
        self.template_plot.setMenuEnabled(False)
        
        # Create scatter plot item for control points with hover effects
        self.scatter = pg.ScatterPlotItem(
            size=15,
            pen=pg.mkPen('b', width=2),
            brush=pg.mkBrush('w'),
            hoverPen=pg.mkPen('r', width=5),
            hoverBrush=pg.mkBrush('r'),
            hoverable=True
        )
        self.template_plot.addItem(self.scatter)
        
        # Create line plot for the curve
        self.curve = self.template_plot.plot(pen='b')
        
        # Connect mouse events
        self.scatter.sigClicked.connect(self._point_clicked)
        self.template_plot.scene().sigMouseClicked.connect(self._plot_clicked)
        self.template_plot.scene().sigMouseMoved.connect(self._mouse_moved)
        
        layout.addWidget(self.template_plot)
        self.setLayout(layout)

    def _update_template(self):
        control_points = self.template_model.get_control_points()
        if len(control_points) < 2:
            return

        # Extract x and y coordinates from control points
        x = np.array([p[0] for p in control_points])
        y = np.array([p[1] for p in control_points])
        
        # Update scatter plot
        self.scatter.setData(x=x, y=y)
        
        # Update curve with raw template data
        x_axis = self.template_model.get_x_axis()
        template_data = self.template_model.get_template_data()
        self.curve.setData(x_axis, template_data)

    def _point_clicked(self, _, points):
        """Handle clicking on existing points"""
        if len(points) > 0:
            if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                # Delete point if Ctrl+Shift+Click (except endpoints)
                index = points[0].index()
                self.plot_clicked_toggle = True
                self.template_model.remove_control_point(index)
                self._update_template()
            elif QApplication.keyboardModifiers() == Qt.ControlModifier:
                # drag point if Ctrl+Click
                self.dragging = True
                self.plot_clicked_toggle = True
                self.current_point_index = points[0].index()
            else:
                self._stop_dragging()

    def _plot_clicked(self, event):
        """Handle clicking on the plot to add new points"""
        if event.button() != 1 or self.dragging:
            return
        
        if self.plot_clicked_toggle:
            self.plot_clicked_toggle = False
            return

        pos = self.template_plot.plotItem.vb.mapSceneToView(event.scenePos())
        x_ms = pos.x()
        y = pos.y()
        
        self.template_model.add_control_point(x_ms, y)
        self._update_template()

    def _mouse_moved(self, pos):
        if not self.dragging or self.current_point_index is None:
            return
            
        pos = self.template_plot.plotItem.vb.mapSceneToView(pos)
        x_ms = pos.x()
        y = pos.y()
        
        self.template_model.update_control_point(self.current_point_index, x_ms, y)
        self._update_template()

    def _stop_dragging(self):
        self.dragging = False
        self.current_point_index = None

    def enable_editing(self, enabled: bool):
        self.template_plot.setEnabled(enabled)

    def _on_duration_changed(self, duration_ms: float):
        self.template_plot.setXRange(0, duration_ms)
        self._update_template()
