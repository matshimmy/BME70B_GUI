from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication
import pyqtgraph as pg
import numpy as np
from PyQt5.QtCore import Qt

class TemplateEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.points = []
        self.dragging = False
        self.current_point_index = None
        self.plot_clicked_toggle = False
        self._build_ui()
        self.reset_template()

    def _build_ui(self):
        layout = QVBoxLayout()
        
        # Create template plot
        self.template_plot = pg.PlotWidget()
        self.template_plot.setBackground('w')
        self.template_plot.setLabel('left', 'Amplitude', units='V')
        self.template_plot.setLabel('bottom', 'Time', units='s')
        self.template_plot.setXRange(0, 1)  # for now
        self.template_plot.setYRange(-1.5, 1.5)  # for now
        
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

    def reset_template(self):
        """Initialize with a flat line"""
        self.points = [
            {'pos': (0, 0), 'data': 1},
            {'pos': (1, 0), 'data': 2}
        ]
        self._update_template()

    def _update_template(self):
        """Update the template visualization"""
        if len(self.points) < 2:
            return

        # Sort points by x position
        self.points.sort(key=lambda p: p['pos'][0])
        
        # Extract x and y coordinates
        x = np.array([p['pos'][0] for p in self.points])
        y = np.array([p['pos'][1] for p in self.points])
        
        # Update scatter plot
        self.scatter.setData(x=x, y=y)
        
        # Create smooth curve using interpolation
        smooth_x = np.linspace(0, 1, 200)
        smooth_y = np.interp(smooth_x, x, y)
        self.curve.setData(smooth_x, smooth_y)

    def _point_clicked(self, _, points):
        """Handle clicking on existing points"""
        if len(points) > 0:
            if QApplication.keyboardModifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
                # Delete point if Ctrl+Shift+Click (except endpoints)
                index = points[0].index()
                if 0 < index < len(self.points) - 1:
                    self.plot_clicked_toggle = True
                    self.points.pop(index)
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
        x = np.clip(pos.x(), 0, 1)
        y = np.clip(pos.y(), -1.5, 1.5)
        
        self.points.append({'pos': (x, y), 'data': len(self.points) + 1})
        self._update_template()

    def _mouse_moved(self, pos):
        """Handle dragging points"""
        if not self.dragging:
            return
            
        pos = self.template_plot.plotItem.vb.mapSceneToView(pos)
        x = np.clip(pos.x(), 0, 1)
        y = np.clip(pos.y(), -1.5, 1.5)
        
        self.points[self.current_point_index]['pos'] = (x, y)
        self._update_template()

    def _stop_dragging(self):
        """Reset dragging state"""
        self.dragging = False
        self.current_point_index = None

    def get_template_data(self):
        """Return the current template data for use in simulation"""
        if len(self.points) < 2:
            return np.zeros(200), np.zeros(200)
            
        x = np.array([p['pos'][0] for p in self.points])
        y = np.array([p['pos'][1] for p in self.points])
        
        smooth_x = np.linspace(0, 1, 200)
        smooth_y = np.interp(smooth_x, x, y)
        
        return smooth_x, smooth_y

    def enable_editing(self, enabled: bool):
        """Enable or disable template editing"""
        self.template_plot.setEnabled(enabled)
