pip install -r requirements.txt
python setup.py sdist
pip install dist/pysonde*.tar.gz

sounding_converter -i $1 -o "{platform}_Radiosonde_{direction}_{date_YYYYMMDDTHHMM}_{location_coord}.nc" -c config/main.yaml 
file_ascent="/Users/admin2/Documents/MPI/pysonde/id_file_ascent.txt"
output_ascent=$(cat "$file_ascent")
file_descent="/Users/admin2/Documents/MPI/pysonde/id_file_descent.txt"
output_descent=$(cat "$file_descent")

sounding_visualize -i $output_ascent
sounding_visualize -i $output_descent
sounding_skewT -i $output_ascent
sounding_compare -i $output_ascent -j $output_descent
sounding_skewT_compare -i $output_ascent -j $output_descent
