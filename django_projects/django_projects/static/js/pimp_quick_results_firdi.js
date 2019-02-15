const pimpQuickResults = (function() {
  let quickResultsManager = {
    init: function(data) {
      this.visibleTableNames = ["peaks_table", "metabolites_table", "pathways_table"];

      // Divvy out the data from the JSON data
      this.rawData = {
        peaks_table: data['peaks'],
        metabolitesPeaks: data['metabolites_peaks'],
        metabolites_table: data['metabolites_names'],
        pathwaysMetabolites: data['pathways_metabolites'],
        pathways_table: data['pathways_names'],
        c_id_to_name: data['comparison_id_to_name'],
        c_id_to_description: data['comparison_id_to_description']
      };

      this.FiRDI = this.initFiRDI(this.rawData);

      preferencesManager.init();
      exportManager.init();

      comparisonLegend.setComparisonLegend(this.rawData['c_id_to_name'], this.rawData['c_id_to_description']);

      // Set the initial number of entries in each table
      this.setInitialCounts(this.rawData);

      // Catch the table clicks to control the info pane content
      this.visibleTableNames.forEach(tableName => $('#' + tableName)
        .DataTable()
        .on('user-select', this.dataTablesDrawFunction));

      // Order the tables
      const peakOrderColumn = $('#peaks_table').DataTable().column('peakSecondaryId:name').index();
      $('#peaks_table').DataTable().order([peakOrderColumn, 'asc']).draw();
      const metaboliteOrderColumn = $('#metabolites_table').DataTable().column('metaboliteName:name').index();
      $('#metabolites_table').DataTable().order([metaboliteOrderColumn, 'asc']).draw();
      const pathwayOrderColumn = $('#pathways_table').DataTable().column('pathwayName:name').index();
      $('#pathways_table').DataTable().order([pathwayOrderColumn, 'asc']).draw();

      return this;
    },
    reloadWithNewData: function(newParameters) {
      // Get a new dataset and reload FiRDI with it. The newParameter should be an object
      // with an attribute-value pair matching a parameter of the quick_results_data_url view.
      // This parameter is embedded in the request.
      $.getJSON(quick_results_data_url, newParameters, data => {

        const newData = {
          'peaks_table': data['peaks'],
          'metabolitesPeaks': data['metabolites_peaks'],
          'metabolites_table': data['metabolites_names'],
          'pathwaysMetabolites': data['pathways_metabolites'],
          'pathways_table': data['pathways_names']
        };

        this.FiRDI.resetFiRDI(newData);
        this.setInitialCounts(newData);
        ['peaks_table', 'metabolites_table', 'pathways_table'].forEach(t => infoPanesManager.clearInfoPane(t));

      });
    },
    getColNames: function() {
      return Object.values(this.rawData['c_id_to_name']);
    },
    makeColNamesForComparisons: function() {
      // this function is for creating the column names for the peak tables comparisons
      const c_names = this.getColNames();
      return c_names.map(x => ({data: x, name: x, title: x}));
    },
    setInitialCounts: function(data) {
      // Set and display the initial number of entries displayed above each table
      this.visibleTableNames.forEach(tableName => tableCounts.setTotalCount(tableName, data));
      // Filtered count is the same as the total count to begin with
      this.visibleTableNames.forEach(tableName => tableCounts.setFilteredCount(tableName, data));
    },
    dataTablesDrawFunction: function(e, dt, type, cell, originalEvent) {
      // calls the appropriate info pane functions
      e.preventDefault();
      const tableId = e.currentTarget.id,
            tables = $('.dataTable').DataTable(),
            tableAPI = tables.table('#' + tableId),
            selectedData = tableAPI.row('.selected').data();

      if (selectedData) {
        infoPanesManager.getEntityInfo(tableId, selectedData);
      } else {
        infoPanesManager.clearInfoPane(tableId);
      }

    },
    initFiRDI: function(rawData) {
      // Config object for FiRDI
      const colNames = this.getColNames();
      const configObject = [
        {
          "tableName": "peaks_table",
          "tableData": rawData["peaks_table"],
          "options": {
            "visible": true,
            "pk": "peakPK"
          },
          "relationship": {"with": "metabolitesPeaks", "using": "peakPK"},
          "otherSettings": {
            "rowCallback": function(row, data, index) {
              // Replace each logFC value with a symbol indicating its change. Arrows indicate a significantly different
              // change direction. Minus signs indicate no statistically significant change.

              colNames.forEach(function(colName) {
                if (data[colName] < 0) {
                  $(row)
                    .find('td:eq(' + (colNames.indexOf(colName) + 3) + ')') // There will always be 3 columns (secondaryId, rt, mass) preceding the first comparison column
                    .html('<span class="glyphicon glyphicon-arrow-down"></span>')
                    .css('color', 'blue')
                } else if (data[colName] > 0) {
                  $(row)
                    .find('td:eq(' + (colNames.indexOf(colName) + 3) + ')') // There will always be 3 columns (secondaryId, rt, mass) preceding the first comparison column
                    .html('<span class="glyphicon glyphicon-arrow-up"></span>')
                    .css('color', 'red')
                } else {
                  $(row)
                    .find('td:eq(' + (colNames.indexOf(colName) + 3) + ')') // There will always be 3 columns (secondaryId, rt, mass) preceding the first comparison column
                    .html('<span class="glyphicon glyphicon-minus"></span>');
                }
              })
            },
            "columns": [
              {
                data: 'peakSecondaryId',
                title: 'ID',
                name: 'peakSecondaryId'
              },
              {
                data: 'rt',
                title: 'rt',
                name: 'rt'
              },
              {
                data: 'mass',
                title: 'mass',
                name: 'mass'
              }].concat(this.makeColNamesForComparisons()),
            "drawCallback": function(settings, json) {
              const api = $('#peaks_table').DataTable();
              $('#peaks_table_count_filtered').text(api.rows().count());
            }
          }
        },
        {
          "tableName": "metabolitesPeaks",
          "tableData": rawData["metabolitesPeaks"],
          "options": {
            "visible": false
          },
          "relationship": {"with": "metabolites_table", "using": "metaboliteSecondaryId"},
        },
        {
          "tableName": "metabolites_table",
          "tableData": this.rawData["metabolites_table"],
          "options": {
            "visible": true,
            "pk": "metaboliteSecondaryId"
          },
          "relationship": {"with": "pathwaysMetabolites", "using": "metaboliteSecondaryId"},
          "otherSettings": {
            "drawCallback": function(settings, json) {
              const api = $('#metabolites_table').DataTable();
              $('#metabolites_table_count_filtered').text(api.rows().count());
            },
            "columns": [
              {
                data: 'metaboliteName',
                name: 'metaboliteName',
                title: 'Name'
              },
              {
                data: 'metabolitePK',
                name: 'metabolitePK',
                title: 'metabolitePK'
              },
              {
                data: 'metaboliteSecondaryId',
                title: 'metaboliteSecondaryId',
                name: 'metaboliteSecondaryId'
              }
            ]
          }
        },
        {
          "tableName": "pathwaysMetabolites",
          "tableData": this.rawData["pathwaysMetabolites"],
          "options": {
            "visible": false
          },
          "relationship": {"with": "pathways_table", "using": "pathwayPK"}
        },
        {
          "tableName": "pathways_table",
          "tableData": rawData["pathways_table"],
          "options": {
            "visible": true,
            "pk": "pathwayPK"
          },
          "otherSettings": {
            "drawCallback": function(settings, json) {
                const api = $('#pathways_table').DataTable();
                $('#pathways_table_count_filtered').text(api.rows().count());
          }}
        }
      ];

      // Custom initialisation options for DataTables via FiRDI
      const defaultDataTablesSettings = {
        "dom": "rpt"
      };

      // Initialise FiRDI
      let out = FiRDI.init(configObject, defaultDataTablesSettings);

      // Hide certain columns
      const columnsToHidePerTable = [
        {"tableName": "peaks_table", "columnNames": ["peakPK"]},
        {"tableName": "metabolites_table", "columnNames": ["metabolitePK", "metaboliteSecondaryId"]},
        {"tableName": "pathways_table", "columnNames": ["pathwayPK"]}
      ];

      columnsToHidePerTable.forEach(function(tableInfo) {
        $('#' + tableInfo['tableName']).DataTable()
          .columns(tableInfo['columnNames'].map(columnName => columnName + ":name")) // append ":name" to each columnName for the selector
          .visible(false);
      });

      return out;
    }
  };

  const preferencesManager = {
    init: function() {
      $('#annotation-type-options :input').change(this.setIdentificationFilterClick.bind(this));
      $('#p-value-adjust-options :input').change(this.setSignificanceFilterClick.bind(this));
      return this;
    },
    dataFilterParameters: {
      'identified': 'false',
      'significant': 'false'
    },
    setIdentificationFilterClick: function() {
      const onlyIdentified = $('#annotation-type-options label.active > input').attr('data-identified');
      this.dataFilterParameters['identified'] = onlyIdentified;
      quickResultsManager.reloadWithNewData(this.dataFilterParameters);
    },
    setSignificanceFilterClick: function() {
      const onlySignificant = $('#p-value-adjust-options label.active > input').attr('data-significant');
      this.dataFilterParameters['significant'] = onlySignificant;
      quickResultsManager.reloadWithNewData(this.dataFilterParameters);
    }
  };

  // table count information
  const tableCounts = {
    // Total count for each table is displayed in the span #tableName_count
    setTotalCount: (tableName, data) => $('#' + tableName + '_count').text(data[tableName].length),
    // Filtered count for each table is displayed in the span #tableName_count_filtered
    setFilteredCount: (tableName, data) => $('#' + tableName + '_count_filtered').text(data[tableName].length),
  };

  const comparisonLegend = {
    setComparisonLegend: function(comparison_id_to_name, comparison_id_to_description) {
      const comparisonIds = Object.keys(comparison_id_to_name);
      const info = comparisonIds
        .map(x => comparison_id_to_name[x] + " = " + comparison_id_to_description[x])
        .join("<br />");
      $('#legend').attr('title', info).tooltip();
    }
  };

  const exportManager = {
    init: function() {
      $('.export-data').click(this.exportData);
    },
    exportData: function() {
        const tableId = $(this).data('table'),
            tableAPI = $('#' + tableId).DataTable(),
            dat = tableAPI.data().toArray();

        alasql("SELECT * INTO TAB('" + tableId + ".tsv') FROM ?", [dat]);
      }
  };

  const infoPanesManager = {
    clearInfoPane: function(tableId) {
      // Wrapper function to call the appropriate info function for the given table/entity
      if (tableId === 'peaks_table') {
        this.clearPeakInfo();
      } else if (tableId === 'metabolites_table') {
        this.clearMetaboliteInfo();
      } else if (tableId === 'pathways_table') {
        this.clearPathwayInfo();
      }
    },
    getEntityInfo: function(tableId, rowObject) {
      // Wrapper function to call the appropriate info function for the given table/entity
      if (tableId === 'peaks_table') {
        this.getPeakInfo(rowObject)
      } else if (tableId === 'metabolites_table') {
        this.getMetaboliteInfo(rowObject);
      } else if (tableId === 'pathways_table') {
        this.getPathwayInfo(rowObject);
      }
    },
    getPeakInfo: function(peakObject) {
      this.clearPeakInfo();

      // Update the peak information column---------------------------------
      const ppm = 3;
      let peakInfo = {'pk': peakObject.peakPK, 'ppm': ppm, 'rtwindow': 120, 'id': peakObject.peakSecondaryId}

      $.getJSON(get_peak_info_url, peakInfo, function(data) {
        peakInfoPanelBody.append('<p>Type: ' + data['type'] + '</p>');
        peakInfoPanelBody.append('<p>Polarity: ' + data['polarity'] + '</p>');
      });

      let peak_info_title = $('<h5/>', {
        'text': 'Peak # ' + peakInfo['id']
      });

      let peakInfoPanelBody = $('#peak-row-info .panel-body').empty();
      peakInfoPanelBody.append(peak_info_title);
      // Make a list-group to organise the plots
      let peak_info_list_group = $('<ul/>', {
        'class': 'list-group'
      });

      // Prepare chromatogram element
      let chromatogram_load_btn = $('<button/>', {
        'class': 'btn btn-sm btn-default chromatogram_load_btn',
        'text': 'Load chromatogram'
      });

      let chromatogram_li = $('<li/>', {
        'class': 'list-group-item',
        'id': 'chromatogram-li',
        'html': chromatogram_load_btn
      });
      peak_info_list_group.append(chromatogram_li);

      // Prepare d3 intensity chart element
      let d3_intensity_chart_load_btn = $('<button/>', {
        'class': 'btn btn-sm btn-default d3_intensity_chart_load_btn',
        'text': 'Load d3 intensity chart'
      });

      let d3_intensity_chart_li = $('<li/>', {
        'class': 'list-group-item',
        'id': 'd3-intensity-chart-li',
        'html': d3_intensity_chart_load_btn
      });
      peak_info_list_group.append(d3_intensity_chart_li);

      $('#peak-row-info .panel').append(peak_info_list_group);

      const createPeaksChromatogram = this.createPeaksChromatogram;
      // Provide buttons to load chromatograms and intensity charts on demand
      // because they are slow to load
      chromatogram_load_btn.click(function() {
        $(this).text("Loading chromatogram...");
        $(this).attr("disabled", "disabled");
        $.getJSON(chromatogram_url, peakInfo, function(data) {
          const chartWidth = $('#peak-row-info .panel-body').width();
          createPeaksChromatogram(chartWidth, chromatogram_li, ppm, data);
        });
      });

      const plotPeakIntensitySamples = this.plotPeakIntensitySamples;
      d3_intensity_chart_load_btn.click(function() {
        $(this).text("Loading intensity chart...");
        $(this).attr("disabled", "disabled");
        plotPeakIntensitySamples(peakInfo, 'd3-intensity-chart-li');
      });
    },
    getMetaboliteInfo: function(metaboliteObject) {
      this.clearMetaboliteInfo();
      if (metaboliteObject['metaboliteName'] != 'No associated metabolite') {
        const metaboliteInfo = {'id': metaboliteObject['metabolitePK']};

        let metabolite_info_div = $('<div/>', {
          'id': 'metabolite_info_div'
        });

        let metabolite_info_title = $('<h5/>', {
          'text': metaboliteObject['metaboliteName']
        });

        metabolite_info_div.append(metabolite_info_title);

        let keggStructureDom = $('<div\>', {
          'html': '<p>Loading chemical structure...</p>'
        });

        $.getJSON(get_kegg_metabolite_info, metaboliteInfo, function(data) {
          const inchikey = data['inchikey'] || 'No Inchikey available';
          metabolite_info_div.append('<p>Inchikey: ' + inchikey + '</p>');
          metabolite_info_div.append('<p>ppm: ' + data['ppm'] + '</p>');
          metabolite_info_div.append('<p>Adduct: ' + data['adduct'] + '</p>');
          let keggStructureImg = $('<img/>', {
            'src': 'http://www.kegg.jp/Fig/compound/' + data['kegg_id'] + '.gif',
            'class': 'img-responsive'
          });
          keggStructureDom.empty().append(keggStructureImg);
          keggStructureDom.append($('<p/>').append($('<a/>', {
            'href': 'http://www.genome.jp/dbget-bin/www_bget?cpd:' + data['kegg_id'],
            'target': '_blank',
            'text': 'Link to KEGG compound database'
          })));
        });

        $('#metabolite-row-info .panel-body').empty();
        $('#metabolite-row-info .panel-body').append(metabolite_info_div);
        $('#metabolite-row-info .panel-body').append(keggStructureDom);
      } else {
        $('#metabolite-row-info .panel-body').text('No associated metabolite that is in in the identified (in the standards) or in the KEGG compound database and has a loss or gain of proton');
      }
    },
    getPathwayInfo: function(pathwayObject) {
      this.clearPathwayInfo();
      if (pathwayObject['pathwayName'] != 'No associated pathway') {
        const pathwayName = pathwayObject['pathwayName'],
              pathwayInfo = {'id': pathwayObject['pathwayPK']};

        var pathway_info_title = $('<h5/>', {
          'text': pathwayName
        });

        var pathwayInfoPane = $('#pathway-row-info .panel-body').empty();
        pathwayInfoPane.append(pathway_info_title);

        $.getJSON(get_pathway_info, pathwayInfo, function(data) {
          pathwayInfoPane.append($('<p/>').append($('<a/>', {
            'href': 'http://www.genome.jp/dbget-bin/www_bget?' + data['pathway_id'],
            'target': '_blank',
            'text': 'Link to KEGG compound database'
          })));
        });
      } else {
        $('#pathway-row-info .panel-body').text('No associated pathway in the KEGG map database');
      }
    },
    clearPeakInfo: function() {
      // Create the divs that make up the 'blank' peak info panel
      var peak_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
      var peak_row_info_title = $('<div/>', {'class': 'panel-heading'});
      var peak_row_info_title_content = $('<h1/>', {
        'class': 'panel-title',
        'id': 'peak-panel-title',
        'text': 'Peak Information'
      });
      var peak_row_info_body_blank = $('<div/>', {
        'text': 'Click a peak above for more information',
        'class': 'panel-body'
      });

      // Combine them
      // Put the title content into the panel title
      peak_row_info_title.append(peak_row_info_title_content)
      // Put the title into the parent panel
      peak_row_info_panel.append(peak_row_info_title)
      // Put the body content into the parent panel
      peak_row_info_panel.append(peak_row_info_body_blank);

      $('#peak-row-info').empty().append(peak_row_info_panel);

    },
    clearMetaboliteInfo: function() {
      // Create the divs that make up the 'blank' metabolite info panel
      var metabolite_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
      var metabolite_row_info_title = $('<div/>', {'class': 'panel-heading'});
      var metabolite_row_info_title_content = $('<h1/>', {
        'class': 'panel-title',
        'id': 'metabolite-panel-title',
        'text': 'Metabolite Information'
      });
      var metabolite_row_info_body_blank = $('<div/>', {
        'text': 'Click a metabolite above for more information',
        'class': 'panel-body'
      });

      // Combine them
      // Put the title content into the panel title
      metabolite_row_info_title.append(metabolite_row_info_title_content)
      // Put the title into the parent panel
      metabolite_row_info_panel.append(metabolite_row_info_title)
      // Put the body content into the parent panel
      metabolite_row_info_panel.append(metabolite_row_info_body_blank);

      $('#metabolite-row-info').empty().append(metabolite_row_info_panel);
    },
    clearPathwayInfo: function() {
      // Create the divs that make up the 'blank' pathway info panel
      var pathway_row_info_panel = $('<div/>', {'class': 'panel panel-default'});
      var pathway_row_info_title = $('<div/>', {'class': 'panel-heading'});
      var pathway_row_info_title_content = $('<h1/>', {
        'class': 'panel-title',
        'id': 'pathway-panel-title',
        'text': 'Pathway Information'
      });
      var pathway_row_info_body_blank = $('<div/>', {
        'text': 'Click a pathway above for more information',
        'class': 'panel-body'
      });

      // Combine them
      // Put the title content into the panel title
      pathway_row_info_title.append(pathway_row_info_title_content)
      // Put the title into the parent panel
      pathway_row_info_panel.append(pathway_row_info_title)
      // Put the body content into the parent panel
      pathway_row_info_panel.append(pathway_row_info_body_blank);

      $('#pathway-row-info').empty().append(pathway_row_info_panel);
    },
    plotPeakIntensitySamples: function(peakInfo, chartDivID) {
      var dataStore = [];
      $.getJSON(get_peak_intensities_url, peakInfo, function(data) {
        // console.log(data);
        var maxOverallIntensity = 0,
            attributes = Object.keys(data);

        attributes.forEach(function(attribute, i) {
          var attributeSamples = data[attribute],
              intensities = d3.values(attributeSamples),
              sampleNames = Object.keys(attributeSamples),
              maxAttributeIntensity = d3.max(intensities),
              sortedIntensities = d3.values(attributeSamples).sort(d3.ascending),
              boxPlotStatistics = {
                lowerquantile: d3.quantile(sortedIntensities, 0.25),
                median: d3.quantile(sortedIntensities, 0.5),
                upperquantile: d3.quantile(sortedIntensities, 0.75),
                mini: d3.min(sortedIntensities),
                maxi: d3.max(sortedIntensities)
              },
              points = [];

          maxOverallIntensity = (maxOverallIntensity > maxAttributeIntensity ? maxOverallIntensity : maxAttributeIntensity);

          // Make x y coordinates
          intensities.forEach(function(d, i) {
            points.push({
              x: attribute,
              y: d,
              z: sampleNames[i],
            });
          });

          dataStore.push({
            attributeName: attribute,
            boxPlotStatistics: boxPlotStatistics,
            points: points
          });
        });

        console.log('d3 munged data', dataStore);

        // d3 margin convention. Make the width and height relative to page components
        var margin = {top: 20, bottom: 75, right: 20, left: 60},
            width = $('#peak-row-info .panel-body').width() - margin.right - margin.left,
            height = $('#results-table-row').height() - margin.top - margin.bottom;

        $('#' + chartDivID).empty();

        // Initialise the svg
        var svg = d3.select("body")
          .select('#' + chartDivID)
          .append("svg")
          .attr('width', width + margin.left + margin.right)
          .attr('height', height + margin.top + margin.bottom)
          .classed("d3-intensity-chart", true);

        // Make the graphing area
        var graph = svg.append('g')
          .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

        // set the x and y scale functions
        var yScale = d3.scaleLinear()
          .domain([0, maxOverallIntensity*1.1]) // add some extra space at the top of the y axis with *1.1
          .range([height, 0]);
        var xScale = d3.scalePoint()
          .domain(attributes)
          .range([0, width])
          .round(true)
          .padding(0.5);

        // x axis
        graph.append('g')
          .attr('transform', 'translate(0,' + height + ')')
          .call(d3.axisBottom(xScale))
          .selectAll("text")
          .attr('y', -5) // rotate and adjust tick positions
          .attr('x', -30)
          .attr('transform', 'rotate(270)');

        // y axis
        graph.append('g')
          .call(d3.axisLeft(yScale)
          .ticks(5, 'e')); // scientific notation

        // y axis label
        svg.append("text")
          .text('Relative intensity')
          .attr('transform', 'translate(' + margin.left/6 +  ',' + (height*0.75) + ') rotate(270)');

        // make a group for each
        var pointStep = xScale.step(),
            horizontalLineWidth = pointStep/4;

        // Functions for mouseover
        function displaySampleName(d, i) {
          var circle = d3.select(this);
          d3.select(this)
            .attr('fill', 'blue')
            .attr('r', 10);

          svg.append('text')
            .attr('id', function() { return 'sample-name-text-' + d.z.split('.')[0]; })
            .attr('x', (width + margin.top + margin.bottom) / 2)
            .attr('y', margin.top)
            .text(function() { return d.z.split('.')[0]; });
        }

        function hideSampleName(d, i) {
          d3.select(this)
            .attr('fill', 'black')
            .attr('r', 3);

          d3.select('#sample-name-text-' + d.z.split('.')[0]).remove();
        }

        var dataSeriesGroups = graph.selectAll('g .data-series-group')
          .data(dataStore)
          .enter()
          .append('g')
          .attr('class', 'data-series-group')
          .attr('id', function(d) { return 'data-series-' + d.attribute; });

        dataSeriesGroups.each(function(attribute, i) {
          var coordinates = attribute.points;
          var boxPlotStatistics = [attribute.boxPlotStatistics],
            g = d3.select(this);

          // Add circles for each data point
          g.selectAll('circle')
            .data(coordinates)
            .enter()
            .append('circle')
            .attr('cx', function(d) { return xScale(d.x); })
            .attr('cy', function(d) { return yScale(d.y); })
            .attr('r', 3)
            .attr('sample-name', function(d) { return d.z; })
            .on('mouseover', displaySampleName)
            .on('mouseout', hideSampleName);

          // Median line
          g.selectAll('line .median-line')
            .data(boxPlotStatistics)
            .enter()
            .append('line')
            .attr('class', 'median-line')
            .attr('x1', xScale(attribute.attributeName) -  horizontalLineWidth)
            .attr('x2', xScale(attribute.attributeName) +  horizontalLineWidth)
            .attr('y1', function(d) { return yScale(d.median); })
            .attr('y2', function(d) { return yScale(d.median); })
            .attr('stroke', 'black');

          // Quantile box
          g.selectAll('rect .quantile-box')
            .data(boxPlotStatistics)
            .enter()
            .append('rect')
            .attr('class', 'quantile-box')
            .attr('x', xScale(attribute.attributeName) - horizontalLineWidth)
            .attr('y', function(d) { return yScale(d.upperquantile); })
            .attr('width', horizontalLineWidth*2)
            .attr('height', function(d) { return (yScale(d.lowerquantile) - yScale(d.upperquantile)); })
            .attr('stroke', 'black')
            .style('fill', 'none');

          // horizontal line for upper whisker
          g.selectAll('line .upper-whisker-horizontal-line')
            .data(boxPlotStatistics)
            .enter()
            .append('line')
            .attr('class', 'upper-whisker-line')
            .attr('x1', function(d) { return xScale(attribute.attributeName) -  horizontalLineWidth; })
            .attr('x2', function(d) { return xScale(attribute.attributeName) +  horizontalLineWidth; })
            .attr('y1', function(d) { return yScale(d.maxi); })
            .attr('y2', function(d) { return yScale(d.maxi); })
            .attr('stroke', 'black');

          // vertical line for upper whisker
          g.selectAll('line .upper-whisker-vertical-line')
            .data(boxPlotStatistics)
            .enter()
            .append('line')
            .attr('class', '.upper-whisker-vertical-line')
            .attr('x1', function(d) { return xScale(attribute.attributeName); })
            .attr('x2', function(d) { return xScale(attribute.attributeName); })
            .attr('y1', function(d) { return yScale(d.lowerquantile); })
            .attr('y2', function(d) { return yScale(d.mini); })
            .attr('stroke', 'black');


          // horizontal line for lower whisker
          g.selectAll('line .lower-whisker-horizonal-line')
            .data(boxPlotStatistics)
            .enter()
            .append('line')
            .attr('class', 'upper-lower-line')
            .attr('x1', function(d) { return xScale(attribute.attributeName) -  horizontalLineWidth; })
            .attr('x2', function(d) { return xScale(attribute.attributeName) +  horizontalLineWidth; })
            .attr('y1', function(d) { return yScale(d.mini); })
            .attr('y2', function(d) { return yScale(d.mini); })
            .attr('stroke', 'black');

          // vertical line for lower whisker
          g.selectAll('line .lower-whisker-vertical-line')
            .data(boxPlotStatistics)
            .enter()
            .append('line')
            .attr('class', '.lower-whisker-vertical-line')
            .attr('x1', function(d) { return xScale(attribute.attributeName); })
            .attr('x2', function(d) { return xScale(attribute.attributeName); })
            .attr('y1', function(d) { return yScale(d.upperquantile); })
            .attr('y2', function(d) { return yScale(d.maxi); })
            .attr('stroke', 'black');
        });
      });
    },
    createPeaksChromatogram: function(chartWidth, div, ppm, response) {
      polarity = response[0][0]
      retentionTime = response[0][1]
      mass = response[0][2]
      // Begining of chart
      $(div).highcharts({
        credits : {
          enabled : false
          },
        chart: {
          zoomType: 'x',
          // spacingRight: 20,
          width: chartWidth,
          height: 400,
          backgroundColor: '#FFFFFF',
          plotBackgroundColor: null,
          plotBorderWidth: null,
          plotShadow: false,
        },
        title: {
          text: 'Peak chromatogram'
        },
        subtitle: {
          text: 'Mass: '+parseFloat(mass).toFixed(4)+' ppm: '+ppm
        },
        exporting: {
          enabled: true,
        },
        xAxis: {
          title: {
            text: 'Retention time (s)'
          },
          showLastLabel: true
        },
        yAxis: {
          title: {
            text: 'Measured abundance'
          },
          min: 0,
        },
        tooltip: {
          shared: true,
          headerFormat: '',
          pointFormat: '<span style="font-size: 10px;font-weight: bold;color:{point.series.color}">{series.name}</span><br/>Retention time: {point.x}<br/>Intensity: {point.y}<br/>'
        },
        legend: {
          enabled: true
        },
        plotOptions: {
          area: {
            marker: {
              enabled: false,
              symbol: 'circle',
              radius: 2,
              states: {
                hover: {
                  enabled: true
                }
              }
          },
          lineWidth: 1,
          shadow: false,
          states: {
            hover: {
              lineWidth: 1
            }
          },
          threshold: null
          },
          series: {
            fillOpacity: 0.1
          }
        },
        series: [{
            type: 'area',
            name: response[1][0],
            data : response[1][1]
        }]
      });
      for (var i=2;i<response.length;i++) {
        $(div).highcharts().addSeries({
          type: 'area',
          name: response[i][0],
          data : response[i][1]
          });
        }
        for (var i=0;i<$(div).highcharts().series.length;i++) {
          if ($(div).highcharts().series[i].data.length == 0) {
            $(div).highcharts().series[i].hide();
          }
        }
      // End of chart
    }
  }

  return {
    init: quickResultsManager.init.bind(quickResultsManager)
  };
})();

$(document).ready(function() {

  $.getJSON(quick_results_data_url, function(data) {

    let pqr = pimpQuickResults.init(data);

  });

});

// TODO graphs of fold changes
// TODO custom metabolite pathway list
// TODO fix clashes e.g. benzoin and aromatic acid
