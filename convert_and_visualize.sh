#pip install -r requirements.txt
#python setup.py sdist
#pip install dist/pysonde*.tar.gz

output_folder="/Volumes/scientists/SO284/data/radiosoundings"

sounding_converter -i $1 -o "$output_folder/{platform}_Radiosonde_{date_YYYYMMDDTHHMM}_{location_coord}_{direction}.nc" -c config/main.yaml 
file_ascent="/Users/admin2/Documents/MPI/pysonde/id_file_ascent.txt"
output_ascent=$(cat "$file_ascent")
file_descent="/Users/admin2/Documents/MPI/pysonde/id_file_descent.txt"
output_descent=$(cat "$file_descent")

sounding_visualize -i $output_ascent -o $output_folder/plots/
sounding_visualize -i $output_descent -o $output_folder/plots/
sounding_skewT -i $output_ascent -o $output_folder/plots/
sounding_compare -i $output_ascent -j $output_descent -o $output_folder/plots/
sounding_skewT_compare -i $output_ascent -j $output_descent -o $output_folder/plots/
